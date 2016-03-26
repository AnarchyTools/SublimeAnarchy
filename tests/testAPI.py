import unittest
import package.sk2p.api as api

#ST3 reloads the API twice for some reason.
if not api.configured(): api.configure()


class APITests(unittest.TestCase):

    def test_complete(self):

        result = api.complete("", 0)
        self.assertGreaterEqual(len(result["key.results"]), 1)

    def test_complete_a(self):
      example = """
class Foo {
    func baz() {

    }
    init(bar: Int) {
        
    }
}

let f = Foo(bar: 2)
f"""
      result = api.complete(example, len(example))

    def test_foundation(self):
      example = """
import Foundation
"""
      result = api.complete(example,len(example))

    def test_docinfo(self):
      example = """let a = "test"
a.hasSuffix("b")"""
      result = api.docInfo(example)

    def test_completion_documentation(self):
      example = """let a = "test"
a."""
      result = api.complete(example, len(example))
      # the key we're looking for is likely key.doc.brief


    def test_documentationForCursorPosition(self):
      example = """let a = "test"
      a.hasSuffix("b")"""
      result = api.documentationForCursorPosition(example, len(example) - 6)

    def test_documentationForCursorPosition_autocomplete(self):
      example = """let a = "test"
a.hasSuffix(suffix: String)"""
      result = api.documentationForCursorPosition(example, len(example) - 15) #this is the position immediately after the left paren
      self.assertTrue(result)

    def test_documentationForCursorPosition_autocomplete_2(self):
      example = """let a = "test"
a.hasSuffix(suffix: String)"""
      result = api.documentationForCursorPosition(example, len(example) - 19) #this is the position in the middle of hasSuffix
      self.assertIn("hasSuffix", result)

    def test_documentationCustom(self):
      example = """class MySpecialClass {
    ///HOW IS THIS EVEN A THING
    func foo() {

    }
}

MySpecialClass().foo()"""
      result = api.documentationForCursorPosition(example, len(example) - 2)
      self.assertIn("HOW IS THIS EVEN", result)

    def test_documentationCustom_2(self):
      example = """///MY AMAZING CLASS
class MySpecialClass {
    ///HOW IS THIS EVEN A THING
    func foo() {

    }
}

let a: MySpecialClass"""
      result = api.documentationForCursorPosition(example, len(example) - 1) #this is the position in the middle of MySpecialClass
      self.assertIn("MY AMAZING CLASS", result)

    @unittest.skip("ObjC documentation isn't supported")
    def test_documentation_Foundation(self):
      example = """import Foundation
try NSFileManager.defaultManager().attributesOfFileSystem(forPath: "2")"""
      result = api.documentationForCursorPosition(example, len(example) - 17) #attributesOfFileSystem
      self.assertTrue(result)

    def test_documentation_extension(self):
      example = """
class MyAmazingClass { }
extension MyAmazingClass {
    /** My great documentation */
    func bar() {

    }
}
let a: MyAmazingClass"""
      result = api.documentationForCursorPosition(example, len(example))

    def test_blank_line(self):
      # crasher
      example = """let a = "test"
a.hasSuffix("foo")

class MyGreatClass {
    
}"""
      result = api.documentationForCursorPosition(example, len(example) - 28)

if __name__ == '__main__':
    unittest.main()
