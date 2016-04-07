import sublime_plugin
import sublime

from .package.sk2p import SK2PAPI
from .package import stTextProcessing
from .package import atpkgTools

def plugin_loaded():
    global settings
    global api
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')
    api = SK2PAPI(settings)

class ShowdocCommand(sublime_plugin.TextCommand):

    def run(self, *args, **kwargs):
        view = self.view
        text = view.substr(sublime.Region(0, view.size()))
        sel = view.sel()
        region1 = sel[0]
        docInfo = api.documentationForCursorPosition(text, region1.begin())
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