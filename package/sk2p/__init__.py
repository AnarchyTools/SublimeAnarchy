"""
sk2p is my arbitrary "sourcekit python bindings" library.

There is an [official binding](https://github.com/apple/swift/tree/master/tools/SourceKit/bindings/python/sourcekitd), but it has several problems:

1.  capi [calls sourcekit.initialize at import-time](https://github.com/apple/swift/blob/swift-DEVELOPMENT-SNAPSHOT-2016-03-24-a/tools/SourceKit/bindings/python/sourcekitd/capi.py#L628), but `Config` is also declared there.  As a result you can't actually configure the import path any way I can determine.
2.  It segfaults a lot on OSX.  I'm not sure why exactly; I spent about 45m investigating it before deciding "nah".
3.  It tries to be more complex about bindings than are strictly needed for SublimeAnarchy (it tries to bridge the whole object model).  I implement (and want to maintain) only those pieces we're actually going to use.
4.  Its imports are not relative and so cannot be vendored inside a sublime plugin easily.

I'm not entirely sure who is using the official bindings or why, but as the scope of the changes we would need ot make became apparent I decided it was easier just to write something in an afternoon, so here it is.
"""

from .api import *
