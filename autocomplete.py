import sublime_plugin
import sublime
from .package.sk2p import SK2PAPI
from .package import stTextProcessing
from .package import atpkgTools

def plugin_loaded():
    global settings
    global api
    settings = sublime.load_settings('SublimeAnarchy.sublime-settings')
    if settings.get('use_sourcekit', False):
        api = SK2PAPI(settings)

class Autocomplete(sublime_plugin.EventListener):

    def enable(self, view):
        global settings
        if not view: return False
        if not view.file_name(): return False
        if not view.file_name().endswith("swift"): return False
        if not settings.get('use_sourcekit', False): return False
        return True

    def on_query_completions(self, view, prefix, locations):
        if not self.enable(view): return []
        text = view.substr(sublime.Region(0, view.size()))
        # look up atpkg if available
        otherSourceFiles = atpkgTools.otherSourceFilesAbs(view.file_name())

        completions = api.complete(text, locations[0], otherSourceFiles=otherSourceFiles)
        sk_completions = []
        for o in completions["key.results"]:
            stPlaceholder = stTextProcessing.fromXcodePlaceholder(o["key.sourcetext"])
            name = o["key.name"]
            #ST does not like completions that start with certain characters
            name = " " + name

            #append type onto the name
            name += "\t" + stTextProcessing.shortType(o["key.kind"])
            sk_completions.append((name, stPlaceholder))
        # completions = [("example", "example"), ("example2\tfoo", "${2:placeholder}example2")]
        print("offering completions",sk_completions)
        return (sk_completions, 0)

    # def on_modified(self, view):
    #     if not self.enable(view): return False
    #     if view.command_history(0):
    #         print(view.command_history(0))
