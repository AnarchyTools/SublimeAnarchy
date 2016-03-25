"""
The api module contains high-level functions like `complete`, that abstract away the syntax of making requests.
Responses are provided as JSON dictionaries in SK format.  Further processing should take place in the plugin package.
"""

from . import cbindings


def complete(sourceText, offset, extraArgs = [], noPlatformArgs = False):
    cbindings.SourceKit.check_loaded()
    if not noPlatformArgs:
        extraArgs.append("-sdk")
        extraArgs.append("/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk")
        #todo: port to Linux etc.

    return cbindings.Request({
        'key.request': cbindings.UIdent('source.request.codecomplete'),
        'key.sourcetext': sourceText,
        'key.offset': offset,
        'key.compilerargs': ['<input>'] + extraArgs
    }).send().toPython()


def configured():
    return cbindings._sk != None

def configure(path = None):
    if path == None:
        # guess!
        # todo: use a more sensible path
        # debugging sourcekit
        path = "/Users/drew/Code/build/Ninja-DebugAssert/swift-macosx-x86_64/lib/sourcekitd.framework/sourcekitd"
        #path = "/Library/Developer/Toolchains/swift-latest.xctoolchain/usr/lib/sourcekitd.framework/sourcekitd"
    from .cbindings import SourceKit
    SourceKit(path)
    assert(configured())


__all__ = ["complete", "configure"]
