import sublime_plugin
import sublime
import json
import random
import xmlrpc.client

import os
import xmlrpc.client
from time import sleep

from subprocess import Popen
from datetime import datetime

from .package import atpkgTools
from .package.atpkg.atpkg_package import Package

debuggers = {} # key = window.id, value lldb proxy

def plugin_loaded():
    global settings
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')

class atdebug(sublime_plugin.WindowCommand):

    def debugger_thread(self, p, port, window):
        project_settings = window.project_data().get('settings', {}).get('SublimeAnarchy', {}).get('debug', {})
        print(project_settings)
        lldb = xmlrpc.client.ServerProxy('http://localhost:' + str(port), allow_none=True)

        project_path = os.path.dirname(window.project_file_name())
        lldb.prepare(
            project_settings.get('executable').replace('${project_path}', project_path),
            project_settings.get('params', []),
            project_settings.get('environment', None),
            project_settings.get('path', None),
            project_settings.get('working_dir', project_path).replace('${project_path}', project_path)
        )
        # while lldb.get_status() != "stopped,signal":
        #     sleep(1)
        #     lldb.start()
        debuggers[window.id()] = lldb

        # polling loop
        try:
            old_status = None
            while True:
                sleep(1)
                new_status = lldb.get_status()
                if old_status != new_status:
                    old_status = new_status
                    print("Status changed:", new_status)
                stdout_buffer = lldb.get_stdout()
                if len(stdout_buffer) > 0:
                    print("STDOUT:", stdout_buffer)
        except Exception as e:
            print("exception", e)
            # so the debug server exited or crashed
            p.wait()

    def _start_debugger(self):
        self._stop_debugger()
        path = os.path.dirname(self.window.project_file_name())
        port = random.randint(12000,13000)
        lldb_server_executable = os.path.join(sublime.packages_path(), "SublimeAnarchy", "package", "lldb_bridge", "lldb_server.py")
        args = ['/usr/bin/python', lldb_server_executable, settings.get('lldb_python_path'), str(port)]
        print("Starting debug server", args)
        p = Popen(args, cwd=path)
        sleep(1)
        threading.Thread(target=self.debugger_thread, name='debugger_thread', args=(p, port, self.window)).start()

    def _stop_debugger(self):
        debugger = debuggers.get(self.window.id(), None)
        if debugger:
            debugger.shutdown_server()        

    def run(self, *args, **kwargs):
        if kwargs.get('start', False):
            self._start_debugger()
        if kwargs.get('stop', False):
            self._stop_debugger()

    def is_enabled(self, *args, **kwargs):
        if self.window.project_file_name():
            if not atpkgTools.findAtpkg(self.window.project_file_name()):
                return False

        if kwargs.get('start', False) and debuggers.get(self.window.id(), None) == None:
            return True

        if kwargs.get('stop', False) and debuggers.get(self.window.id(), None) != None:
            return True
        return False


class atlldb(sublime_plugin.TextCommand):

    def save_breakpoints(self, lldb):
        project_data = self.view.window().project_data()
        breakpoints = lldb.get_breakpoints()
        for bp in breakpoints:
            del bp['id']
        if 'settings' not in project_data:
            project_data['settings'] = {}
        if 'SublimeAnarchy' not in project_data['settings']:
            project_data['settings']['SublimeAnarchy'] = {}
        project_data['settings']['SublimeAnarchy']['breakpoints'] = breakpoints
        self.view.window().set_project_data(project_data)

    def load_breakpoints(self, lldb):
        breakpoints = self.view.window().project_data().get('settings', {}).get('SublimeAnarchy', {}).get('breakpoints', [])
        lldb.delete_all_breakpoints()
        for bp in breakpoints:
            bp_id = lldb.set_breakpoint(bp['file'], bp['line'], bp['condition'], bp['ignore_count'])
            if not bp['enabled']:
                lldb.disable_breakpoint(bp_id)

    def _disable_breakpoint(self, lldb, bp):
        breakpoints = lldb.get_breakpoints()
        for lldb_bp in breakpoints:
            if lldb_bp['file'] == bp['file'] and lldb_bp['line'] == bp['line']:
                lldb.disable_breakpoint(lldb_bp['id'])
        self.save_breakpoints(lldb)

    def _enable_breakpoint(self, lldb, bp):
        breakpoints = lldb.get_breakpoints()
        for lldb_bp in breakpoints:
            if lldb_bp['file'] == bp['file'] and lldb_bp['line'] == bp['line']:
                lldb.enable_breakpoint(lldb_bp['id'])
        self.save_breakpoints(lldb)

    def _create_breakpoint(self, lldb, file, line):
        lldb.set_breakpoint(file, line, None, 0)
        self.save_breakpoints(lldb)

    def _remove_breakpoint(self, lldb, bp):
        breakpoints = lldb.get_breakpoints()
        for lldb_bp in breakpoints:
            if lldb_bp['file'] == bp['file'] and lldb_bp['line'] == bp['line']:
                lldb.delete_breakpoint(lldb_bp['id'])
        self.save_breakpoints(lldb)

    def toggle_breakpoint(self, lldb):
        breakpoints = self.view.window().project_data().get('settings', {}).get('SublimeAnarchy', {}).get('breakpoints', [])

        cursor = self.view.sel()[0].begin()
        row, col = self.view.rowcol(cursor)

        found = False
        for bp in breakpoints:
            if bp['file'] == self.view.file_name() and bp['line'] == row:
                self._remove_breakpoint(lldb, bp)
                found = True
        if not found:
            self._create_breakpoint(lldb, self.view.file_name(), row)
        update_markers(self.view)

    def enable_disable_breakpoint(self, lldb):
        breakpoints = self.view.window().project_data().get('settings', {}).get('SublimeAnarchy', {}).get('breakpoints', [])

        cursor = self.view.sel()[0].begin()
        row, col = self.view.rowcol(cursor)

        found = False
        for bp in breakpoints:
            if bp['file'] == self.view.file_name() and bp['line'] == row and bp['enabled'] == True:
                self._disable_breakpoint(lldb, bp)
                found = True
            elif bp['file'] == self.view.file_name() and bp['line'] == row and bp['enabled'] == False:
                self._enable_breakpoint(lldb, bp)
                found = True
        update_markers(self.view)

    def run(self, *args, **kwargs):
        lldb = debuggers.get(self.view.window().id(), None)
        if kwargs.get('toggle_breakpoint', False):
            self.toggle_breakpoint(lldb)
        if kwargs.get('enable_disable_breakpoint', False):
            self.enable_disable_breakpoint(lldb)

    def is_enabled(self, *args, **kwargs):
        if "source.swift" in self.view.scope_name(0) and self.view.window().project_file_name():
            if not atpkgTools.findAtpkg(self.view.window().project_file_name()):
                return False
        if not debuggers.get(self.view.window().id(), None):
            return False
        return True

class LLDBBreakPointHighlighter(sublime_plugin.EventListener):

    def enable(self, view):
        if not view: return False
        if "source.swift" not in view.scope_name(0): return False
        return True

    def on_activated(self, view):
        if not self.enable(view):
            return
        update_markers(view)

def update_markers(view):
    breakpoints = view.window().project_data().get('settings', {}).get('SublimeAnarchy', {}).get('breakpoints', [])
    enabled_markers = []
    disabled_markers = []
    for bp in breakpoints:
        if bp['file'] == view.file_name():
            location = view.line(view.text_point(bp['line'], 0))
            if bp['enabled']:
                enabled_markers.append(location)
            else:
                disabled_markers.append(location)
    view.add_regions("breakpoint_enabled", enabled_markers, "breakpoint_enabled", "Packages/SublimeAnarchy/images/breakpoint_enabled.png", sublime.HIDDEN)
    view.add_regions("breakpoint_disabled", disabled_markers, "breakpoint_disabled", "Packages/SublimeAnarchy/images/breakpoint_disabled.png", sublime.HIDDEN)
