"""
The api module contains high-level functions like `complete`, that abstract away the syntax of making requests.
Responses are provided as JSON dictionaries in SK format.  ST-specific processing should take place in the plugin package.
"""

from . import cbindings

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
        # print("offering request", request)
        return cbindings.Request(request).send().toPython()

    def __preparePlatformArgs(self, extraArgs, noPlatformArgs):
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
        # print("sending request", request)
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

    def editorOpen(self, sourceText, extraArgs = [], otherSourceFiles = [], noPlatformArgs = False):
        """This apparently parses the source file."""
        extraArgs = self.__preparePlatformArgs(extraArgs, noPlatformArgs)
        return cbindings.Request({
          "key.request": cbindings.UIdent("source.request.editor.open"),
          "key.name": "DoesItMatter",
          "key.sourcetext":sourceText
        }).send().toPython()

    def cursorInfoOffset(self, sourceText, offset, extraArgs = [], otherSourceFiles = [], noPlatformArgs = False):
        """An undocumented SK 'cursorInfo' request, which mostly seems to query documentation for a particular offset."""
        # This request only works when given a real file.  I don't know why.
        # The request is not actually documented, so I'm not sure if upstream considers this a bug or expected behavior
        # in any event, let's write sourcetext out to a tempfile and try that way.
        import tempfile
        temp = tempfile.NamedTemporaryFile(mode="w")
        temp.write(sourceText)
        temp.flush()
        extraArgs = self.__preparePlatformArgs(extraArgs, noPlatformArgs)
        result = cbindings.Request({
          "key.request": cbindings.UIdent("source.request.cursorinfo"),
          "key.compilerargs": [temp.name] + otherSourceFiles + extraArgs,
          "key.sourcefile" : temp.name,
          "key.offset":offset
        }).send().toPython()
        temp.close()
        return result

    def documentationForCursorPosition(self, sourceText, offset, otherSourceFiles = [], extraArgs = [], noPlatformArgs = False):
        if offset >= len(sourceText): raise Exception("offset must be less than", len(sourceText))
        if offset < 0:
            return None
        info = self.cursorInfoOffset(sourceText, offset, extraArgs, otherSourceFiles, noPlatformArgs)
        if "key.doc.full_as_xml" in info:
            return info["key.doc.full_as_xml"]

        #look for a result earlier in the string, but not a newline:
        searchOffset = offset
        while searchOffset >= 0 and sourceText[searchOffset] != "\n":
            test = self.cursorInfoOffset(sourceText, searchOffset, otherSourceFiles, extraArgs, noPlatformArgs)
            if "key.doc.full_as_xml" in test:
                return test["key.doc.full_as_xml"]
            searchOffset -= 1

        # if we're located inside an "identifier", this may be a case of Swift latching onto the arguments..
        # they might be invalid, for example, in the case where we have just accepted an autocompletion.
        # try removing them
        sourceTextInfo = self.editorOpen(sourceText, extraArgs, otherSourceFiles, noPlatformArgs)
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
                test = self.cursorInfoOffset(revisedText, searchOffset, extraArgs, otherSourceFiles, noPlatformArgs)
                if "key.doc.full_as_xml" in test:
                    return test["key.doc.full_as_xml"]
                searchOffset -= 1

        # todo: look at objc documentation

        # Give up looking for documentation
        return None