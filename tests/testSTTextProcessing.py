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

if __name__ == '__main__':
    unittest.main()
