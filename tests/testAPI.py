import unittest
from package.sk2p import SK2PAPI
import os.path

settings = {
    "sourcekit_path": "/Library/Developer/Toolchains/swift-latest.xctoolchain/usr/lib/sourcekitd.framework/sourcekitd",
    "sourcekit_sdk": "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk",
}
api = SK2PAPI(settings)

class TestComplete(unittest.TestCase):

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

    def test_completion_documentation(self):
      example = """let a = "test"
a."""
      result = api.complete(example, len(example))
      # the key we're looking for is likely key.doc.brief

    def test_multifile_complete(self):
      example = ""
      loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
      aSwiftPath = os.path.join(loc, "fixtures/sampleatpkg/src/a.swift")
      bSwiftPath = os.path.join(loc, "fixtures/sampleatpkg/src/b.swift")

      result = api.complete(example, 0, otherSourceFiles = [aSwiftPath, bSwiftPath])
      self.assertEqual(len(list(filter(lambda x: x["key.name"] == "ThisSymbolIsDefinedInASwift", result["key.results"]))), 1)
      self.assertEqual(len(list(filter(lambda x: x["key.name"] == "ThisSymbolIsDefinedInBSwift", result["key.results"]))), 1)

class TestDocumentation(unittest.TestCase):

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
      result = api.documentationForCursorPosition(example, len(example) - 1)

    def test_blank_line(self):
      # crasher
      example = """let a = "test"
a.hasSuffix("foo")

class MyGreatClass {
    
}"""
      result = api.documentationForCursorPosition(example, len(example) - 28)

    @unittest.skip("SR-1096")
    def test_multifile_documentation(self):
      example = "let a: ThisSymbolIsDefinedInASwift"
      loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
      aSwiftPath = os.path.join(loc, "fixtures/sampleatpkg/src/a.swift")
      bSwiftPath = os.path.join(loc, "fixtures/sampleatpkg/src/b.swift")

      result = api.documentationForCursorPosition(example, len(example) - 1, otherSourceFiles = [aSwiftPath, bSwiftPath])

    def test_cursorInfo_offset(self):
      example = """class MySpecialClass {
    ///HOW IS THIS EVEN A THING
    func foo() {

    }
}

MySpecialClass().foo()"""
      result = api.cursorInfoOffset(example, len(example) - 3)
      self.assertIn("HOW IS THIS EVEN", result["key.doc.full_as_xml"])
    

if __name__ == '__main__':
    unittest.main()
