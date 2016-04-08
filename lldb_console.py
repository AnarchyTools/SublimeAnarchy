import sublime_plugin
import sublime

import os

from .debug import debuggers, status_callbacks, output_callbacks, retry
from .package import atpkgTools
from .package.atpkg.atpkg_package import Package

window_layouts = {}

def update_stack(window, status):
    lldb = debuggers[window.id()]
    if not lldb:
        return

    view = None
    for v in window.views():
        if v.name() == "LLDB Stack":
            view = v
            break
    if not view:
        return


    with retry():
        bt = lldb.get_backtrace()
    print(bt)

    buf = ""
    for thread_id, frames in bt.items():
        buf += "Thread {}\n".format(thread_id)
        buf += "-" * (len(buf) - 1) + "\n"

        frame_id = 0
        for frame in frames:
            if frame['line'] != 0:
                buf += "{id: <5}{module: <30}{file}:{line} ({function})".format(
                    id=frame_id,
                    module=frame['module'],
                    file=os.path.basename(frame['file']),
                    line=frame['line'],
                    function=frame['function']
                )
            else:
                buf += "{id: <5}{module: <30}{symbol}".format(
                    id=frame_id,
                    module=frame['module'],
                    symbol=frame['symbol']
                )
            buf += "\n"
            frame_id += 1

    view.run_command("update_lldb_stack", { "data": buf })

def update_console(window, buf):
    view = None
    for v in window.views():
        if v.name() == "LLDB Console":
            view = v
            break
    if not view:
        return

    view.run_command("update_lldb_console", { "data": "STDOUT: " + buf })


class updateLldbConsole(sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        data = kwargs.get("data", "")
        last_line = self.view.line(self.view.size())
        line = self.view.substr(last_line)

        self.view.replace(edit, last_line, data)
        self.view.insert(edit, self.view.size(), line)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(self.view.size(), self.view.size()))

    def is_visible(self):
        return False

class updateLldbStack(sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        data = kwargs.get("data", "")
        region = sublime.Region(0, self.view.size())
        self.view.replace(edit, region, data)
        self.view.sel().clear()
        self.view.set_syntax_file('Packages/SublimeAnarchy/build_output.sublime-syntax')

    def is_visible(self):
        return False

class atdebugConsole(sublime_plugin.WindowCommand):
               
    def _show_console(self):
        window_layouts[self.window.id()] = self.window.get_layout()
        self.window.set_layout({
            "cols": [0, 0.5, 1],
            "rows": [0, 0.5, 1],
            "cells": [[0, 0, 1, 2], [1, 0, 2, 1],
                                    [1, 1, 2, 2]]
        })
        self.window.focus_group(1)
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name('LLDB Stack')
        view.set_syntax_file('Packages/SublimeAnarchy/lldb_stack.sublime-syntax')
        status_callbacks[self.window.id()].append(update_stack)

        self.window.focus_group(2)
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name('LLDB Console')
        view.set_syntax_file('Packages/SublimeAnarchy/lldb_console.sublime-syntax')
        output_callbacks[self.window.id()].append(update_console)
        view.run_command("update_lldb_console", { "data": "(lldb) " })

        self.window.focus_group(0)

    def _hide_console(self):
        for view in self.window.views():
            if view.name() in ["LLDB Console", "LLDB Stack"]:
                self.window.focus_view(view)
                self.window.run_command("close_file")
        self.window.set_layout(window_layouts[self.window.id()])
        del window_layouts[self.window.id()]

    def run(self, *args, **kwargs):
        if kwargs.get('show', False):
            self._show_console()
        else:
            self._hide_console()

    def is_enabled(self, *args, **kwargs):
        if self.window.project_file_name():
            if not atpkgTools.findAtpkg(self.window.project_file_name()):
                return False

        if kwargs.get('show', False) and debuggers.get(self.window.id(), None) != None:
            return True

        if not kwargs.get('show', False) and window_layouts.get(self.window.id(), None) != None:
            return True

        return False
