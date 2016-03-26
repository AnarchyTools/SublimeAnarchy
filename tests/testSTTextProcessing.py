import unittest
import os
import json

import package.stTextProcessing as st

completions = None
loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
with open(os.path.join(loc, "sample-completions.json")) as f:
    completions = f.read()
completions = json.loads(completions)
class TextProcessingTests(unittest.TestCase):

    def test_completion_placeholders(self):
        for completion in completions["key.results"]:
            st.fromXcodePlaceholder(completion["key.sourcetext"])

    def test_simple_placeholder(self):
        self.assertEqual("#file", st.fromXcodePlaceholder("#file"))

    def test_placeholder_2(self):
        self.assertEqual("alignof(${0:T.Type})", st.fromXcodePlaceholder("alignof(<#T##T.Type#>)"))

    def test_placeholder_3(self):
        self.assertEqual(st.fromXcodePlaceholder("debugPrint(<#T##items: Any...##Any#>)"), "debugPrint(${0:items: Any...})")

    def test_placeholder_4(self):
        self.assertEqual(st.fromXcodePlaceholder("stride(from: <#T##T#>, through: <#T##T#>, by: <#T##T.Stride#>)"), "stride(from: ${0:T}, through: ${1:T}, by: ${2:T.Stride})")
    
    def test_shortTypes(self):
        for completion in completions["key.results"]:
            st.shortType(completion["key.kind"])

    def test_xmlDoc(self):
        sampleDoc = "<Function><Name>hasSuffix(_:)</Name><USR>s:FSS9hasSuffixFSSSb</USR><Declaration>func hasSuffix(suffix: String) -&gt; Bool</Declaration><Abstract><Para>Returns <codeVoice>true</codeVoice> iff <codeVoice>self</codeVoice> ends with <codeVoice>suffix</codeVoice>.</Para></Abstract></Function>"
        self.assertEqual(st.fromXMLDoc(sampleDoc), "<pre>func hasSuffix(suffix: String) -&gt; Bool</pre><p>Returns <pre>true</pre> iff <pre>self</pre> ends with <pre>suffix</pre>.</p>")

    def test_xmlDoc_quotes(self):
        sampleDoc = """<Other><Name>endIndex</Name><USR>s:vSS8endIndexVVSS13CharacterView5Index</USR><Declaration>var endIndex: Index { get }</Declaration><Abstract><Para>The &quot;past the end&quot; position in <codeVoice>self.characters</codeVoice>.</Para></Abstract><Discussion><Para><codeVoice>endIndex</codeVoice> is not a valid argument to <codeVoice>subscript</codeVoice>, and is always reachable from <codeVoice>startIndex</codeVoice> by zero or more applications of <codeVoice>successor()</codeVoice>.</Para></Discussion></Other>"""
        output = st.fromXMLDoc(sampleDoc)
        self.assertEqual(output,'<pre>var endIndex: Index { get }</pre><p>The "past the end" position in <pre>self.characters</pre>.</p>')
if __name__ == '__main__':
    unittest.main()
