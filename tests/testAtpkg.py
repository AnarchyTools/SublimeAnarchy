import unittest
import package.atpkgTools as tools
import tempfile
import os.path
import os
class FindAtpkg(unittest.TestCase):
    def test_find(self):
        path = tempfile.mkdtemp()
        atbuildFile = os.path.join(path, "build.atpkg")
        with open(atbuildFile, "w") as f:
            f.write("hello world")
        result = tools.findAtpkg(os.path.join(path,"foo.swift"))
        self.assertEqual(result, atbuildFile)

    def test_dontfind(self):
        path = tempfile.mkdtemp()
        result = tools.findAtpkg(os.path.join(path,"foo.swift"))
        self.assertEqual(result, None)

    def test_findHard(self):
        path = tempfile.mkdtemp()
        atbuildFile = os.path.join(path, "build.atpkg")

        foo1 = os.path.join(path,"foo1")
        foo2 = os.path.join(foo1,"foo2")
        foo3 = os.path.join(foo2,"foo3")

        os.makedirs(foo3)
        with open(atbuildFile, "w") as f:
            f.write("hello world")
        result = tools.findAtpkg(os.path.join(foo3,"foo.swift"))
        self.assertEqual(result, atbuildFile)

    def test_findatpkg_single(self):
        loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        aSwiftPath = os.path.join(loc, "fixtures/singleSourceFileAtpkg/foo.swift")
        atpkg = tools.taskForSourceFile(aSwiftPath)
        self.assertTrue(atpkg)

class TestParsing(unittest.TestCase):
    def test_parse(self):
        loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        buildAtpkgPath = os.path.join(loc, "fixtures/sampleatpkg/build.atpkg")
        import package.atpkg.atpkg_package
        p = package.atpkg.atpkg_package.Package.fromFile(buildAtpkgPath)
        task = p.__dict__["tasks"]["default"]
        sources = task.collect_sources()
        self.assertEqual(len(sources), 3)
        self.assertIn('src/a.swift', sources)
        self.assertIn('src/b.swift', sources)
        self.assertIn('extra/foo.swift', sources)

    def test_argparser(self):
        loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        import package.atpkg.atpkg_package
        buildAtpkgPath = os.path.join(loc, "fixtures/sampleatpkg/build.atpkg")

        p = package.atpkg.atpkg_package.Package.fromFile(buildAtpkgPath)
        task = p.__dict__["tasks"]["default"]
        result =tools.absPathArgParser(["-I","whatever/foo"],task)
        self.assertTrue(result[1].endswith("SublimeAnarchy/tests/fixtures/sampleatpkg/whatever/foo"))

class TestLookups(unittest.TestCase):
    def test_tasklookup(self):
        loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        aSwiftPath = os.path.join(loc, "fixtures/sampleatpkg/src/a.swift")
        self.assertTrue(tools.taskForSourceFile(aSwiftPath))

    def test_sourcelookup(self):
        loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        aSwiftPath = os.path.join(loc, "fixtures/sampleatpkg/src/a.swift")
        otherSources = tools.otherSourceFilesAbs(aSwiftPath)
        self.assertIn(os.path.join(loc, "fixtures/sampleatpkg/src/b.swift"),otherSources)
        self.assertIn(os.path.join(loc, "fixtures/sampleatpkg/extra/foo.swift"),otherSources)

    def test_sourcelookup_noatpkg(self):
        loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        aSwiftPath = os.path.join(loc, "fixtures/noatpkg/foo.swift")
        otherSources = tools.otherSourceFilesAbs(aSwiftPath)
        self.assertEqual(otherSources,[])
    def test_sourcelookup_single(self):
        loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        aSwiftPath = os.path.join(loc, "fixtures/singleSourceFileAtpkg/foo.swift")
        otherSources = tools.otherSourceFilesAbs(aSwiftPath)
        self.assertEqual(otherSources,[])