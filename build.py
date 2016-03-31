import sublime_plugin
import sublime

import threading
import os
from subprocess import Popen, PIPE, STDOUT

from .package import atpkgTools
from .package.atpkg.atpkg_package import Package

def plugin_loaded():
    global settings
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')

class atbuild(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        tool = kwargs.get("tool", "atllbuild")
        if not self.window.project_file_name():
            return

        pkg = Package.fromFile(atpkgTools.findAtpkg(self.window.project_file_name()))   
        probable_task = pkg.task_for_file(self.window.active_view().file_name())

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

    def build(self, pkg, tasks, index):
        if index == -1:
            return
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

    def run(self):
        print("Selected " + self.task)
        path = os.path.dirname(atpkgTools.findAtpkg(self.window.project_file_name()))
        atbuild = os.path.expanduser(settings.get('atbuild_path', 'atbuild'))
        p = Popen([atbuild, self.task], stdout=PIPE, stderr=STDOUT, cwd=path)
        output, error = p.communicate()
        print(output.decode('utf-8'))
