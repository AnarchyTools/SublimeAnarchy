import sublime_plugin
import sublime
import SublimeAnarchy.package.sk2p.api as api
from .package import stTextProcessing
# ST3 loads the plugin twice for some ridiculous reason
if not api.configured(): api.configure()


class Autocomplete(sublime_plugin.EventListener):

    def enable(self, view):
        if not view: return False
        if not view.file_name().endswith("swift"): return False
        return True

    def on_query_completions(self, view, prefix, locations):
        if not self.enable(view): return []
        text = view.substr(sublime.Region(0, view.size()))

        completions = api.complete(text, locations[0])
        sk_completions = []
        for o in completions["key.results"]:
            stPlaceholder = stTextProcessing.fromXcodePlaceholder(o["key.sourcetext"])
            name = o["key.name"]
            #ST does not like completions that start with certain characters
            name = " " + name

            #append type onto the name
            name += "\nFoo"
            name += "\t" + stTextProcessing.shortType(o["key.kind"])
            sk_completions.append((name, stPlaceholder))
        # completions = [("example", "example"), ("example2\tfoo", "${2:placeholder}example2")]
        print("offering completions",sk_completions)
        return (sk_completions, 0)

    # def on_modified(self, view):
    #     if not self.enable(view): return False
    #     if view.command_history(0):
    #         print(view.command_history(0))

    def on_selection_modified_async(self,view):
        if not self.enable(view): return []
        text = view.substr(sublime.Region(0, view.size()))
        sel = view.sel()
        region1 = sel[0]
        docInfo = api.documentationForCursorPosition(text, region1.begin())
        if not docInfo: return
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
