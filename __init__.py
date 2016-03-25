import sublime_plugin
import sublime
import SublimeAnarchy.package.sk2p.api as api
from .package import stTextProcessing
# ST3 loads the plugin twice for some ridiculous reason
if not api.configured(): api.configure()


class Autocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if not view: return
        if not view.file_name().endswith("swift"): return []
        text = view.substr(sublime.Region(0, view.size()))

        completions = api.complete(text, locations[0])
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

    def on_modified(self, view):
        if not view: return
        if not view.file_name().endswith("swift"): return
        if view.command_history(0):
            print(view.command_history(0))
