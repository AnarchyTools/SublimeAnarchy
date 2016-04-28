import sublime_plugin
import sublime
from .package.sk2p import SK2PAPI
from .package import stTextProcessing
from .package import atpkgTools
import threading
import os.path

def plugin_loaded():
    global settings
    global api
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')
    if settings.get('use_sourcekit', False):
        api = SK2PAPI(settings)

class Autocomplete(sublime_plugin.EventListener):

    def __init__(self):
        self.recent_completions = []
        self.stack_overflow = False

    def enable(self, view):
        global settings
        if not view: return False
        if not view.file_name(): return False
        if not view.file_name().endswith("swift"): return False
        if not settings.get('use_sourcekit', False): return False
        return True

    def async_completions(self, view, prefix, locations):
        text = view.substr(sublime.Region(0, view.size()))
        # look up atpkg if available
        atpkg = atpkgTools.findAtpkg(view.file_name())
        otherSourceFiles = atpkgTools.otherSourceFilesAbs(view.file_name())
        atpkgBase = os.path.dirname(atpkg)
        completions = api.complete(text, locations[0], otherSourceFiles=otherSourceFiles, extraArgs = ["-I", atpkgBase+"/.atllbuild/products/"])
        sk_completions = []
        for o in completions["key.results"]:
            stPlaceholder = stTextProcessing.fromXcodePlaceholder(o["key.sourcetext"])
            name = o["key.name"]
            #ST does not like completions that start with certain characters
            name = " " + name

            #append type onto the name
            name += "\t" + stTextProcessing.shortType(o["key.kind"])
            sk_completions.append((name, stPlaceholder))
        self.recent_completions = sk_completions
        print("Completions arrived")
        self.stack_overflow = True
        view.run_command("hide_auto_complete")
        view.run_command("auto_complete", {
            'disable_auto_insert': True,
            'api_completions_only': False,
            'next_completion_if_showing': False,
            'auto_complete_commit_on_tab': True,
        })
        self.stack_overflow = False


    def on_query_completions(self, view, prefix, locations):
        if not self.enable(view): return ([], 0)

        if not self.recent_completions:
            if self.stack_overflow:
                return ([], 0)
            t = threading.Thread(target=self.async_completions, args=(view,prefix,locations))
            t.start()
            print("No completions right now; trying async")
            return ([], 0)
        else:
            completions = self.recent_completions
            self.recent_completions = None
            print("offering completions",completions)
            return (completions, 0)

    # def on_modified(self, view):
    #     if not self.enable(view): return False
    #     if view.command_history(0):
    #         print(view.command_history(0))
