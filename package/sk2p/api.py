"""
The api module contains high-level functions like `complete`, that abstract away the syntax of making requests.
Responses are provided as JSON dictionaries in SK format.  ST-specific processing should take place in the plugin package.
"""

from . import cbindings

import tempfile
import os

# If you show cursorInfo a different file, it caches it.  
# If we call it on cursor move (or several times in some cases!) memory usage grows to 
# hundreds of GB.  Just another "fun" day in SK land.
# to defeat this, we use a global variable.  Always use the same temporary file for the lifetime of the program.

# Fun fact: We never actually write to this file.  I'm not sure if SK does "for us" or not.  
# We do *tell SK* we're writing to the file, which seems to be close enough.

# I tried the behavior of actually writing to the file, but it turns out SK is pretty inconsistent about
# whether it goes out to disk or relies on its own cache of the file.  So by going through SK rather than out
# to disk, we ensure its consistent cache state, which fixes several of our tests.
cursorInfoTempFile = tempfile.mkstemp()[1]

class SK2PAPI(object):

    def __init__(self, settings):
        self.settings = settings
        sk_path = settings.get("sourcekit_path", None)
        if not sk_path:
            raise Exception("Please setup sourcekit_path in settings")
        setattr(cbindings, "_sk", cbindings.SourceKit(sk_path))
        super().__init__()

    def complete(self, sourceText, offset, otherSourceFiles = [], extraArgs = [], noPlatformArgs = False):
        extraArgs = self.__preparePlatformArgs(extraArgs, noPlatformArgs)
        request = {
            'key.request': cbindings.UIdent('source.request.codecomplete'),
            'key.sourcetext': sourceText,
            'key.offset': offset,
            'key.compilerargs': ['<input>'] + extraArgs + otherSourceFiles
        }
        return cbindings.Request(request).send().toPython()

    def __preparePlatformArgs(self, extraArgs, noPlatformArgs):
        extraArgs = list(extraArgs)
        if "sdk" in extraArgs:
            # If we end up in a python method that recurses (several of them do), we sometimes analyze
            # the same file different times.  We want to make sure we use the same arguments in all cases
            # so that SKS can share memory between several analyses.  Failure to do this can cause MASSIVE
            # allocations inside SKS, which seems to treat inputs with different compiler arguments as different inputs.
            raise Exception("Too many SDKs; this will overflow.")
        if not noPlatformArgs:
            extraArgs.append("-sdk")
            sdk_path = self.settings.get("sourcekit_sdk", None)
            if not sdk_path:
                raise Exception("Please setup sourcekit_sdk path in settings")
            extraArgs.append(sdk_path)
            #todo: port to Linux etc.
        return extraArgs



    def docInfo(self, sourceText, extraArgs = [], otherSourceFiles = [], noPlatformArgs = False):
        """This somewhat poorly named API returns the *document* info."""
        extraArgs = self.__preparePlatformArgs(extraArgs, noPlatformArgs)
        request = {
              "key.request": cbindings.UIdent("source.request.docinfo"),
              "key.sourcetext": sourceText,
              "key.compilerargs": ['<input>'] + extraArgs + otherSourceFiles,
              "key.sourcefile" : "<input>"
        }
        return cbindings.Request(request).send().toPython()

    def __findAnnotationForSourceText(self, sourceText, offset, annotations, acceptClosest = False):
        closestDistance = 999999999
        closestMatch = None
        for annotation in annotations:
            a_offset = annotation["key.offset"]
            if abs(offset - a_offset) < closestDistance:
                closestDistance = abs(offset - a_offset)
                closestMatch = annotation
            if a_offset <= offset:
                a_length = annotation["key.length"]
                rhs = a_offset + a_length
                if abs(offset - rhs) < closestDistance:
                    closestDistance = abs(offset - rhs)
                    closestMatch = annotation
                if rhs >= offset:
                    return annotation
        if acceptClosest:
            return closestMatch
        return None

    def __annotationBefore(self, cursorPosition, annotations):
        """Returns the first annotation at or before the given cursor position.  Assumes an ordered list of annotations."""
        for annotation in reversed(annotations):
            a_offset = annotation["key.offset"]
            a_length = annotation["key.length"]
            if a_offset <= cursorPosition:
                return annotation

    def cursorInfoUsr(self, sourceText, usr, extraArgs = [], otherSourceFiles = [], noPlatformArgs = False):
        """An undocumented SK 'cursorInfo' request, which mostly seems to query documentation for a particular USR."""
        extraArgs = self.__preparePlatformArgs(extraArgs, noPlatformArgs)
        return cbindings.Request({
          "key.request": cbindings.UIdent("source.request.cursorinfo"),
          "key.sourcetext": sourceText,
          "key.compilerargs": ['<input>'] + otherSourceFiles + extraArgs,
          "key.sourcefile" : "<input>",
          "key.usr":usr
        }).send().toPython()

    def editorClose(self, sourceFile):
        return cbindings.Request({
              "key.request": cbindings.UIdent("source.request.editor.close"),
              "key.name": sourceFile,
            }).send().toPython()

    def editorOpen(self, sourceText, sourceName, closeAfterwards = True):
        """This apparently parses the source file."""
        result = cbindings.Request({
          "key.request": cbindings.UIdent("source.request.editor.open"),
          "key.name": sourceName,
          "key.sourcetext":sourceText
        }).send().toPython()
        # don't allocate gigs and gigs of memory, lol
        if closeAfterwards:
            self.editorClose(sourceName)
        return result

    def replaceText(self, sourceText, sourceFile, offset, length):
        request = {
            "key.request": cbindings.UIdent("source.request.editor.replacetext"),
            "key.name": sourceFile,
            "key.offset": offset,
            "key.length": length,
            "key.sourcetext": sourceText
        }
        result = cbindings.Request(request).send().toPython()
        return result

    def cursorInfoOffset(self, sourceText, offset, extraArgs = [], otherSourceFiles = [], noPlatformArgs = False):
        """An undocumented SK 'cursorInfo' request, which mostly seems to query documentation for a particular offset."""
        # This request only works when given a real file (not sourcetext).  I don't know why.
        # The request is not actually documented, so I'm not sure if upstream considers this a bug or expected behavior
        # in any event, let's tell SK we're using a tempfile and try that way.
        cursorInfoTempFile = "/tmp/imaginary-file.swift"
        extraArgs = self.__preparePlatformArgs(extraArgs, noPlatformArgs)
        #"replace" the "file"
        # I think this basically tells SK we opened the file
        self.editorOpen("", cursorInfoTempFile, closeAfterwards = False)
        # Here we're telling SK we're replacing the contents of the file with something new
        # note that the length we're replacing is zero here, because earlier we told SK we opened an empty file.  lol
        # todo: can we just open the file "already" instead of replacing the text?
        replaceResult = self.replaceText(sourceText, cursorInfoTempFile, 0, 0)
        request = {
          "key.request": cbindings.UIdent("source.request.cursorinfo"),
          "key.compilerargs": [cursorInfoTempFile] + otherSourceFiles + extraArgs,
          "key.sourcefile" : cursorInfoTempFile,
          "key.offset":offset
        }
        result = cbindings.Request(request).send().toPython()
        # we let SK know we're done with the file
        self.editorClose(cursorInfoTempFile)

        #os.remove(cursorInfoTempFile)
        return result

    def documentationForCursorPosition(self, sourceText, offset, otherSourceFiles = [], extraArgs = [], noPlatformArgs = False):
        extraArgs = self.__preparePlatformArgs(extraArgs, noPlatformArgs)
        if offset >= len(sourceText): raise Exception("offset must be less than", len(sourceText))
        if offset < 0:
            return None
        info = self.cursorInfoOffset(sourceText, offset, extraArgs, otherSourceFiles, noPlatformArgs = True)
        if "key.doc.full_as_xml" in info:
            return info["key.doc.full_as_xml"]

        #look for a result earlier in the string, but not a newline:
        searchOffset = offset
        while searchOffset >= 0 and sourceText[searchOffset] != "\n":
            test = self.cursorInfoOffset(sourceText, searchOffset, otherSourceFiles, extraArgs, noPlatformArgs = True)
            if "key.doc.full_as_xml" in test:
                return test["key.doc.full_as_xml"]
            searchOffset -= 1

        # if we're located inside an "identifier", this may be a case of Swift latching onto the arguments..
        # they might be invalid, for example, in the case where we have just accepted an autocompletion.
        # try removing them
        sourceTextInfo = self.editorOpen(sourceText, "AT:documentationForCursorPosition")
        annotation = self.__findAnnotationForSourceText(sourceText, offset, sourceTextInfo["key.syntaxmap"])

        if not annotation: return None #no annotation, give up
        
        if annotation["key.kind"] == "source.lang.swift.syntaxtype.identifier":
            #first, let's try to remove just the stuff coming after the current identifier.
            #this handles the case where we have e.g.
            # a.foo(INVALID STUFF)
            #    ^
            # and we turn that to
            # a.foo
            searchOffset = offset
            while True:
                earlierAnnotation = self.__annotationBefore(searchOffset, sourceTextInfo["key.syntaxmap"])
                if not earlierAnnotation: break
                searchOffset = earlierAnnotation["key.offset"]
                revisedText = sourceText[:searchOffset+earlierAnnotation["key.length"]]
                test = self.cursorInfoOffset(revisedText, searchOffset, extraArgs, otherSourceFiles, noPlatformArgs = True)
                if "key.doc.full_as_xml" in test:
                    return test["key.doc.full_as_xml"]
                searchOffset -= 1

        # todo: look at objc documentation

        # Give up looking for documentation
        return None