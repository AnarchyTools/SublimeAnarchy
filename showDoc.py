import sublime_plugin
import sublime
import os.path

from .package.sk2p import SK2PAPI
from .package import stTextProcessing
from .package import atpkgTools

def plugin_loaded():
    global settings
    global api
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')
    if settings.get('use_sourcekit', False):
        api = SK2PAPI(settings)

class ShowdocCommand(sublime_plugin.TextCommand):

    def run(self, *args, **kwargs):
        view = self.view
        text = view.substr(sublime.Region(0, view.size()))
        sel = view.sel()
        region1 = sel[0]
        # look up atpkg if available
        atpkg = atpkgTools.findAtpkg(view.file_name())
        otherSourceFiles = atpkgTools.otherSourceFilesAbs(view.file_name())
        atpkgBase = os.path.dirname(atpkg)

        docInfo = api.documentationForCursorPosition(text, region1.begin(), otherSourceFiles = otherSourceFiles, extraArgs = ["-I", atpkgBase+"/.atllbuild/products/"])
        if not docInfo: 
            sublime.status_message("No documentation available for cursor position.")
            return
        processedDoc = stTextProcessing.fromXMLDoc(docInfo)
        #wrap in a style
        processedDoc = """<style>
    html {
    background-color: #232628;
    color: #CCCCCC;
    }

    body {
    font-size: 14px;
    font-family: Palatino;
    }
    pre {
    font-size: 13px;
    font-family: Menlo;
    }

    a {
    color: #6699cc;
    }

    b {
    color: #cc99cc;
    }

    h1 {
    color: #99cc99;
    font-size: 14px;
    }
    </style>""" + processedDoc + ""
        view.show_popup(processedDoc, on_navigate=print)

    def is_enabled(self, *args, **kwargs):
        global settings
        return settings.get('use_sourcekit', False)
