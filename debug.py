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

markers = {} # key = window.id, value array of markers
debuggers = {} # key = window.id, value lldb proxy

def plugin_loaded():
    global settings
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')

class atdebug(sublime_plugin.WindowCommand):

    def debugger_thread(self, p, window):
        with open(self.window.project_file_name(), "r") as fp:
            data = fp.read()
        project_settings = json.loads(data).get('settings', {}).get('SublimeAnarchy', {}).get('debug', {})
        with xmlrpc.client.ServerProxy('http://localhost:12597', allow_none=True) as lldb:
            lldb.prepare(
                project_settings.get('executable'),
                project_settings.get('params', []),
                project_settings.get('environment', None),
                project_settings.get('path', None),
                project_settings.get('working_dir', os.path.dirname(self.window.project_file_name()))
            )
            while lldb.get_status() != "stopped,signal":
                sleep(1)
                lldb.start()
            debuggers[window.id()] = lldb
            p.wait()

    def run(self, *args, **kwargs):
        old_debugger = debuggers.get(self.window.id(), None)
        if old_debugger:
            old_debugger.shutdown_server()

        path = os.path.dirname(self.window.project_file_name())
        port = random.randint(12000,13000)
        lldb_server_executable = os.path.join(sublime.packages_path(), "SublimeAnarchy", "package", "lldb_bridge", "lldb_server.py")
        p = Popen(['/usr/bin/python', lldb_server_executable, settings.lldb_python_path, str(port)], cwd=path)
        threading.Thread(target=self.debugger_thread, name='debugger_thread', args=(p, self.window)).start()

    def is_enabled(self, *args, **kwargs):
        if self.window.project_file_name():
            return atpkgTools.findAtpkg(self.window.project_file_name()) != None
        return False


class atlldb(sublime_plugin.TextCommand):

    def toggle_breakpoint(self, lldb):
        pass

    def enable_disable_breakpoint(self, lldb):
        pass

    def run(self, *args, **kwargs):
        lldb = debuggers.get(self.view.window().id(), None)
        if not lldb:
            return

        if kwargs.get('toggle_breakpoint', False):
            self.toggle_breakpoint(lldb)
        if kwargs.get('enable_disable_breakpoint', False):
            self.enable_disable_breakpoint(lldb)

    def is_enabled(self, *args, **kwargs):
        if "source.swift" in self.view.scope_name(0) and self.view.window().project_file_name():
            return atpkgTools.findAtpkg(self.view.window().project_file_name()) != None
        return False

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
    pass