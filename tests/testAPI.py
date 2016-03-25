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
      
if __name__ == '__main__':
    unittest.main()
