import sublime_plugin
import sublime

import threading
import os
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime

from .package import atpkgTools
from .package.atpkg.atpkg_package import Package

markers = {}
markers_updated = {}
markers_view_updated = {}
last_build_target = {}

def plugin_loaded():
    global settings
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')

class atbuild(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        tool = kwargs.get("tool", "atllbuild")
        build_last = kwargs.get("build_last", False)
        if not self.window.project_file_name():
            return

        pkg = Package.fromFile(atpkgTools.findAtpkg(self.window.project_file_name()))   
        probable_task = pkg.task_for_file(self.window.active_view().file_name())

        if not build_last:
            tasks = []
            idx = 0
            for (name, task) in pkg.tasks.items():
                if task.tool != tool:
                    continue
                desc = "Task group"
                if task.tool == "atllbuild":
                    desc = "Compile Swift " + task.output_type.replace("-", " ")
                elif task.tool == "shell":
                    desc = "Run Shell script"
                elif task.tool == "xctestrun":
                    desc = "Execute Tests"
                if task == probable_task:
                    idx = len(tasks)
                tasks.append([name, desc])

            if len(tasks) == 0:
                sublime.message_dialog("SublimeAnarchy\n\nThere are no tasks to run")
                return

            if len(tasks) == 1:
                self.build(pkg, tasks, 0)
                return

            self.window.show_quick_panel(tasks, lambda x: self.build(pkg, tasks, x), 0, idx)
        else:
            if self.window.id() in last_build_target:
                BuildWithATBuild(self.window, pkg, last_build_target[self.window.id()]).start()

    def build(self, pkg, tasks, index):
        if index == -1:
            return
        for view in self.window.views():
            if view.file_name():
                view.run_command("save")
        last_build_target[self.window.id()] = tasks[index][0]
        BuildWithATBuild(self.window, pkg, tasks[index][0]).start()

    def is_enabled(self, *args, **kwargs):
        if self.window.project_file_name():
            return atpkgTools.findAtpkg(self.window.project_file_name()) != None
        return False

class BuildWithATBuild(threading.Thread):

    def __init__(self, window, pkg, task):
        self.window = window
        self.pkg = pkg
        self.task = task
        threading.Thread.__init__(self)

    @staticmethod
    def read_stream(stream, view):
        for line in stream:
            view.run_command("append_output_panel", { "data": line.decode('utf-8') })
        if not stream.closed:
            stream.close()

    def run(self):
        # create or clear output panel
        view = self.window.find_output_panel("atbuild")
        if not view:
            view = self.window.create_output_panel("atbuild")
        markers[self.window.id()] = []
        markers_updated[self.window.id()] = datetime.now()

        view.run_command("update_output_panel", { "data": "" })
        self.window.run_command("show_panel", { "panel": "output.atbuild" })

        # start build process
        path = os.path.dirname(atpkgTools.findAtpkg(self.window.project_file_name()))
        atbuild = os.path.expanduser(settings.get('atbuild_path', 'atbuild'))
        p = Popen([atbuild, self.task], stdout=PIPE, stderr=PIPE, cwd=path)

        # wait to finish and update output panel
        threading.Thread(target=self.read_stream, name='read_stdout', args=(p.stdout, view)).start()
        threading.Thread(target=self.read_stream, name='read_stderr', args=(p.stderr, view)).start()
        p.wait()

        for view in self.window.views():
            check_update(view)


class updateOutputPanel(sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        data = kwargs.get("data", "")
        region = sublime.Region(0, self.view.size())
        self.view.set_read_only(False)
        self.view.replace(edit, region, data)
        self.view.set_read_only(True)
        self.view.sel().clear()
        self.view.set_syntax_file('Packages/SublimeAnarchy/build_output.sublime-syntax')
        self.view.erase_regions("mark_info")
        self.view.erase_regions("mark_warning")
        self.view.erase_regions("mark_error")

    def is_visible(self):
        return False

class appendOutputPanel(sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        data = kwargs.get("data", "")
        self.view.set_read_only(False)
        self.view.insert(edit, self.view.size(), data)
        self.view.set_read_only(True)
        #self.view.sel().clear()

    def is_visible(self):
        return False

class JumpToCompilerError(sublime_plugin.EventListener):

    def enable(self, view):
        if not view: return False
        if "source.atbuild_output" not in view.scope_name(0): return False
        return True

    def on_selection_modified(self, view):
        if not self.enable(view):
            return
        if len(list(view.sel())) == 0:
            return
        cursor = view.sel()[0].begin()
        if "filename" in view.scope_name(cursor):
            line = view.substr(view.line(cursor))
            parts = [p.strip() for p in line.split(":", maxsplit=5)]

            filename = os.path.join(os.path.dirname(view.window().project_file_name()), parts[0])
            view.window().open_file(filename + ":" + parts[1] + ":" + parts[2], sublime.ENCODED_POSITION)

    def on_modified(self, view):
        if not self.enable(view):
            return

        cursor = view.size()
        line = view.line(cursor - 1) 
        if "filename" in view.scope_name(line.begin()):
            line_text = view.substr(line)
            parts = [p.strip() for p in line_text.split(":", maxsplit=5)]
            filename = os.path.join(os.path.dirname(view.window().project_file_name()), parts[0])

            marker = "info"
            if "error:" in line_text:
                marker = "error"
            elif "warning:" in line_text:
                marker = "warning"

            if view.window().id() not in markers:
                markers[view.window().id()] = []

            # save the marker
            markers[view.window().id()].append({
                "type": marker,
                "file": filename,
                "panel_line": line,
                "row": int(parts[1]) - 1,
                "col": int(parts[2]) - 1,
                "text": parts[4],
            })
            markers_updated[view.window().id()] = datetime.now()

            # update view
            rgn = {"error": [], "info": [], "warning": []}
            for marker in markers[view.window().id()]:
                rgn[marker['type']].append(marker["panel_line"])
            for (key, value) in rgn.items():
                view.add_regions("mark_" + key, value, "mark_" + key, "Packages/SublimeAnarchy/images/" + key + ".png", sublime.HIDDEN)


class BuildErrorHilighter(sublime_plugin.EventListener):

    def enable(self, view):
        if not view: return False
        if "source.swift" not in view.scope_name(0): return False
        return True

    def on_activated(self, view):
        if not self.enable(view):
            return
        check_update(view)

    def on_selection_modified_async(self, view):
        if not self.enable(view):
            return
        
        for region in ["build_warning", "build_error"]: 
            for warn in view.get_regions(region):
                if not warn.intersects(view.sel()[0]):
                    continue

                for marker in markers.get(view.window().id(), []):
                    location = view.line(view.text_point(marker['row'], marker['col']))
                    if location.intersects(warn):
                        view.show_popup(marker['text'])
                        return

def update_markers(view):
    # collect markers
    rgn = {"error": [], "info": [], "warning": []}
    for marker in markers.get(view.window().id(), []):
        if marker['file'] != view.file_name():
            continue
        location = view.text_point(marker['row'], marker['col'])
        line = view.line(location)
        found = False
        for m in rgn[marker['type']]:
            if m == line:
                found = True
                break
        if not found:
            rgn[marker['type']].append(line)

    # send to sublime
    for (key, value) in rgn.items():
        view.add_regions("build_" + key, value, "build_" + key, "Packages/SublimeAnarchy/images/" + key + ".png", sublime.HIDDEN)

def check_update(view):
    # check if a region update is needed
    output_panel = view.window().find_output_panel("atbuild")
    if output_panel:
        last_update = markers_view_updated.get(view.id(), None)
        last_build = markers_updated.get(view.window().id(), datetime.now())
        if not last_update or last_update < last_build:
            markers_view_updated[view.id()] = last_build
            update_markers(view)
