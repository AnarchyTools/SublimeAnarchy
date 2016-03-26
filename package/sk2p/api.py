"""
The api module contains high-level functions like `complete`, that abstract away the syntax of making requests.
Responses are provided as JSON dictionaries in SK format.  ST-specific processing should take place in the plugin package.
"""

from . import cbindings


def complete(sourceText, offset, extraArgs = [], noPlatformArgs = False):
    extraArgs = __preparePlatformArgs(extraArgs, noPlatformArgs)
    cbindings.SourceKit.check_loaded()

    return cbindings.Request({
        'key.request': cbindings.UIdent('source.request.codecomplete'),
        'key.sourcetext': sourceText,
        'key.offset': offset,
        'key.compilerargs': ['<input>'] + extraArgs
    }).send().toPython()

def __preparePlatformArgs(extraArgs, noPlatformArgs):
    if not noPlatformArgs:
        extraArgs.append("-sdk")
        extraArgs.append("/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk")
        #todo: port to Linux etc.
    return extraArgs


def configured():
    return cbindings._sk != None

def configure(path = None):
    if path == None:
        # guess!
        # todo: use a more sensible path
        # debugging sourcekit
        #path = "/Users/drew/Code/build/Ninja-DebugAssert/swift-macosx-x86_64/lib/sourcekitd.framework/sourcekitd"
        path = "/Library/Developer/Toolchains/swift-latest.xctoolchain/usr/lib/sourcekitd.framework/sourcekitd"
    from .cbindings import SourceKit
    SourceKit(path)
    assert(configured())

def docInfo(sourceText, extraArgs = [], noPlatformArgs = False):
    """This somewhat poorly named API returns the *document* info."""
    extraArgs = __preparePlatformArgs(extraArgs, noPlatformArgs)
    return cbindings.Request({
          "key.request": cbindings.UIdent("source.request.docinfo"),
          "key.sourcetext": sourceText,
          "key.compilerargs": ['<input>'] + extraArgs,
          "key.sourcefile" : "<input>"
    }).send().toPython()

def __findAnnotationForSourceText(sourceText, offset, annotations, acceptClosest = False):
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


# def documentationForSourceText(sourceText, offset, extraArgs = [], noPlatformArgs = False):
#     # first, we get the docInfo
#     docInfo = self.docInfo(sourceText, extraArgs, noPlatformArgs)
#     # we find an annotation at the requested cursor position
#     annotation = __findAnnotationForSourceText(docInfo["key.annotations"], offset)
#     if not annotation: return None
#     # look up the module

def cursorInfo(sourceText, usr, extraArgs = [], noPlatformArgs = False):
    """An undocumented SK 'cursorInfo' request, which mostly seems to query documentation for a particular USR."""
    extraArgs = __preparePlatformArgs(extraArgs, noPlatformArgs)
    return cbindings.Request({
      "key.request": cbindings.UIdent("source.request.cursorinfo"),
      "key.sourcetext": sourceText,
      "key.compilerargs": ['<input>'] + extraArgs,
      "key.sourcefile" : "<input>",
      "key.usr":usr
    }).send().toPython()

def documentationForCursorPosition(sourceText, offset, extraArgs = [], noPlatformArgs = False, tryKeepingIdentifier = True):
    sourceTextInfo = docInfo(sourceText, extraArgs, noPlatformArgs)
    annotation = __findAnnotationForSourceText(sourceText, offset, sourceTextInfo["key.annotations"])
    if not annotation: 
        # If there was no annotation at the exact location, can we find an annotation at a close location?
        annotation = __findAnnotationForSourceText(sourceText, offset, sourceTextInfo["key.annotations"], acceptClosest = True)
        if annotation:
            #okay, let's back up to the last annotation we understand and try the docInfo again
            #this is commonly used to get around e.g. `a.appendString(` (where docInfo does not like that trailing `(`
            revisedText = sourceText[:annotation["key.offset"] + annotation["key.length"]]
            if offset > len(revisedText): revisedOffset = len(revisedText)
            return documentationForCursorPosition(revisedText, revisedOffset, extraArgs, noPlatformArgs)
    if not "key.usr" in annotation: 
        # if what we found is an "identifier", then this may be a case of Swift latching onto the arguments..
        # they might be invalid, for example, in the case where we have just accepted an autocompletion.
        if annotation["key.kind"] == "source.lang.swift.syntaxtype.identifier":
            revisedOffset = offset

            if tryKeepingIdentifier: # don't stack overflow by continuing to try a failing strategy
                #first, let's try to remove just the stuff coming after the current identifier.
                #this handles the case where we have e.g.
                # a.foo(INVALID STUFF)
                #    ^
                # and we turn that to
                # a.foo
            
                revisedText = sourceText[:annotation["key.offset"] + annotation["key.length"]]
                if offset > len(revisedText): revisedOffset = len(revisedText)
                attempt = documentationForCursorPosition(revisedText, revisedOffset, extraArgs, noPlatformArgs, tryKeepingIdentifier = False)
                if attempt: return attempt

            #Right, so that didn't work.  What if we got stuck in the argument itself?  e.g.
            # a.foo(INVALID STUFF)
            #           ^
            # we still want
            # a.foo
            # in that case, so let's try removing the entire identifer

            revisedText = sourceText[:annotation["key.offset"]]
            if offset > len(revisedText): revisedOffset = len(revisedText)
            return documentationForCursorPosition(revisedText, revisedOffset, extraArgs, noPlatformArgs)
        return None
            
    #okay, we have a usr.  Maybe we already have the entity for this usr?
    if "key.entities" in sourceTextInfo:
        #flatten all the entities with a recursive descent parser
        def rdp(items):
            allKids = []
            for item in items:
                if "key.entities" in item:
                    allKids += rdp(item["key.entities"])
                    del item["key.entities"] #don't duplicate
                allKids += [item]
            return allKids
        entities = rdp(sourceTextInfo["key.entities"])
        entity = filter(lambda x: "key.usr" in x and x["key.usr"] == annotation["key.usr"], entities)
        for entity in entity:
            if "key.doc.full_as_xml" in entity:
                return entity["key.doc.full_as_xml"]
            return None

    # Nope.  Check cursorInfo for clues
    info = cursorInfo(sourceText, annotation["key.usr"], extraArgs, noPlatformArgs)
    if "key.doc.full_as_xml" in info:
        return info["key.doc.full_as_xml"]

    # todo: look at objc documentation

    # Give up looking for documentation
    return None

__all__ = ["complete", "configure"]
