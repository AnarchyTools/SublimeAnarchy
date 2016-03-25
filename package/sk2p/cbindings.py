"""
The cbindings module interfaces with SK and creates SK-"like" objects and bridges them to Python.
Generally, the python API exposed tries to stay quite close to the C "object model".
We expose an object for most of the underlying C objects, and handle the memory management details of those objects.
"""

from ctypes import cdll, c_char_p, c_void_p, POINTER, c_size_t, c_int64, c_int, Structure, c_bool
import json

"""# Stores the SourceKit singleton"""
_sk = None


class SourceKit(object):

    """The SourceKit singleton.  This handles startup/shutdown behavior of the underlying SK engine."""

    def __init__(self, path):
        if _sk:
            raise Exception("Can't re-initialize SourceKit.")
        self._lib = cdll.LoadLibrary(path)

        # I have learned some rules about how to avoid segfaults in my time.
        # 1.  Always declare an argtype and a restype for any function used
        # 2.  argtypes should use class names if available, rather than raw c_void_p.  (Thus implement `from_param` on those types)
        # 3.  return types should use c_void_p NOT native types.  AND **IN PARTICULAR**, any function with a c_void_p
        #     return type MUST be wrapped in c_void_p at invocation.  e.g.
        #     c_void_p(self._lib.my_void_p_func())
        # Abandon these rules at your peril.

        # These functions come from sourcekitd.h

        self._lib.sourcekitd_initialize.argtypes = []
        self._lib.sourcekitd_initialize.restype = None

        self._lib.sourcekitd_shutdown.argtypes = []
        self._lib.sourcekitd_shutdown.restype = None

        self._lib.sourcekitd_uid_get_from_cstr.argtypes = [c_char_p]
        self._lib.sourcekitd_uid_get_from_cstr.restype = c_void_p

        self._lib.sourcekitd_uid_get_string_ptr.argtypes = [c_void_p]
        self._lib.sourcekitd_uid_get_string_ptr.restype = c_char_p

        self._lib.sourcekitd_request_dictionary_create.argtypes = [POINTER(c_void_p), POINTER(c_void_p), c_size_t]
        self._lib.sourcekitd_request_dictionary_create.restype = c_void_p

        self._lib.sourcekitd_request_release.argtypes = [c_void_p]
        self._lib.sourcekitd_request_release.restype = None

        self._lib.sourcekitd_request_dictionary_set_uid.argtypes = [Dictionary, UIdent, UIdent]
        self._lib.sourcekitd_request_dictionary_set_uid.restype = None

        self._lib.sourcekitd_request_dictionary_set_string.argtypes = [Dictionary, UIdent, c_char_p]
        self._lib.sourcekitd_request_dictionary_set_string.restype = None

        self._lib.sourcekitd_request_dictionary_set_int64.argtypes = [Dictionary, UIdent, c_int64]
        self._lib.sourcekitd_request_dictionary_set_int64.restype = None

        self._lib.sourcekitd_send_request_sync.argtypes = [Request]
        self._lib.sourcekitd_send_request_sync.restype = c_void_p

        self._lib.sourcekitd_response_is_error.argtypes = [Response]
        self._lib.sourcekitd_response_is_error.restype = c_bool

        self._lib.sourcekitd_request_dictionary_set_value.argtypes = [Dictionary, UIdent, c_void_p]
        self._lib.sourcekitd_request_dictionary_set_value.restype = None

        self._lib.sourcekitd_request_dictionary_set_uid.argtypes = [Dictionary, UIdent, UIdent]
        self._lib.sourcekitd_request_dictionary_set_uid.restype = None

        self._lib.sourcekitd_request_uid_create.argtypes = [UIdent]
        self._lib.sourcekitd_request_uid_create.restype = c_void_p

        self._lib.sourcekitd_request_retain.argtypes = [c_void_p]
        self._lib.sourcekitd_request_retain.restype = None

        self._lib.sourcekitd_response_dispose.argtypes = [Response]
        self._lib.sourcekitd_response_dispose.restype = None

        self._lib.sourcekitd_response_error_get_description.argtypes = [Response]
        self._lib.sourcekitd_response_error_get_description.restype = c_char_p

        self._lib.sourcekitd_request_array_create.argtypes = [POINTER(c_void_p), c_size_t]
        self._lib.sourcekitd_request_array_create.restype = c_void_p

        self._lib.sourcekitd_request_array_set_string.argtypes = [c_void_p, c_size_t, c_char_p]
        self._lib.sourcekitd_request_array_set_string.restypes = None

        self._lib.sourcekitd_response_get_value.argtypes = [Response]
        self._lib.sourcekitd_response_get_value.restype = VariantStructure

        self._lib.sourcekitd_variant_json_description_copy.argtypes = [VariantStructure]
        self._lib.sourcekitd_variant_json_description_copy.restype = c_char_p

        self._lib.sourcekitd_variant_get_type.argtypes = [VariantStructure]
        self._lib.sourcekitd_variant_get_type.restype = c_int

        self._lib.sourcekitd_response_description_dump.argtypes = [c_void_p]
        self._lib.sourcekitd_response_description_dump.restype = None

        self._lib.sourcekitd_response_description_copy.argtypes = [Response]
        self._lib.sourcekitd_response_description_copy.restype = c_char_p

        global _sk
        _sk = self

        self._lib.sourcekitd_initialize()

    def __del__(self):
        self._lib.sourcekitd_shutdown()

    @staticmethod
    def check_loaded():
        if not _sk:
            raise Exception("SourceKit not configured.  Please run .configure before using sk2p")


class Array(object):

    """A SourceKit array object"""

    def __init__(self, arr):
        self._obj = c_void_p(_sk._lib.sourcekitd_request_array_create(POINTER(c_void_p)(), 0))
        i = 0
        for o in arr:
            if isinstance(o, str):
                _sk._lib.sourcekitd_request_array_set_string(self._obj, -1, o.encode("utf-8"))
            else:
                raise Exception("Not implemented array type %s" % o)
            i += 1

    def __del__(self):
        _sk._lib.sourcekitd_request_release(self._obj)

    def from_param(self):
        return self._obj

    def as_ptr(self):
        return self._obj


class UIdent(object):

    """What SourceKit calls a `uid`.  This is essentially a "special" kind of string."""

    def __init__(self, key):
        self._obj = c_void_p(_sk._lib.sourcekitd_uid_get_from_cstr(key.encode('utf-8')))

    def __str__(self):
        return "<UIdent: " + _sk._lib.sourcekitd_uid_get_string_ptr(self._obj).decode("utf-8") + ">"

    def from_param(self):
        return self._obj


class Dictionary(object):

    """A SourceKit-backed Dictionary"""
    strongPointers = []

    def __init__(self, dictRepresentation):
        self._obj = c_void_p(_sk._lib.sourcekitd_request_dictionary_create(
            POINTER(c_void_p)(), POINTER(c_void_p)(), 0))
        for k, v in dictRepresentation.items():
            if isinstance(v, UIdent):
                _sk._lib.sourcekitd_request_dictionary_set_uid(self, UIdent(k), v)
            elif isinstance(v, str):
                _sk._lib.sourcekitd_request_dictionary_set_string(self, UIdent(k), v.encode("utf-8"))
            elif isinstance(v, int):
                _sk._lib.sourcekitd_request_dictionary_set_int64(self, UIdent(k), v)
            elif isinstance(v, list):
                arr = Array(v)
                self.strongPointers.append(arr)

                _sk._lib.sourcekitd_request_dictionary_set_value(self, UIdent(k), arr.as_ptr())
            else:
                raise Exception("Not implemented v type %s" % v)

    def __del__(self):
        _sk._lib.sourcekitd_request_release(self._obj)

    def from_param(self):
        return self._obj


class Request(object):

    """
    This is a request object.  There's no direct SK equivalent, but
    we distinguish between Requests vs some of other kind of dict you
    may have lying around (like a parameter)
    """

    def __init__(self, requestDict):
        self.__dict = Dictionary(requestDict)

    def send(self):
        resp = Response(c_void_p(_sk._lib.sourcekitd_send_request_sync(self)))
        resp.dont_gc_request = self
        return resp

    def from_param(self):
        return self.__dict.from_param()


class VariantStructure(Structure):
    """
    This is the underlying structure called `sourcekitd_variant_t` in SK
    """
    _fields_ = [("data", c_int64 * 3)]


class Variant(object):
    """
    This is a Python conception of a SK "variant" object.
    Its underlying representation is VariantStructure, but it offended
    my inner C programmer to put methods onto a C struct.
    """

    def __init__(self, response):
        self._obj = _sk._lib.sourcekitd_response_get_value(response)
        self._response = response  # don't GC response

    def __str__(self):
        result = _sk._lib.sourcekitd_variant_json_description_copy(self._obj)
        with open("/tmp/test.json", "wb") as f:
            f.write(result)
        return result.decode("mac-roman") #ugh

    def from_param(self):
        return self._obj


class Response(object):
    """
    An SK response object.
    """
    def __init__(self, o):
        self._obj = o
        if _sk._lib.sourcekitd_response_is_error(self):
            errorstr = _sk._lib.sourcekitd_response_error_get_description(self).decode("utf-8")
            raise Exception("sourcekit reported error: " + errorstr)

    def from_param(self):
        return self._obj

    def __str__(self):
        return "<Response %s>" % _sk._lib.sourcekitd_response_description_copy(self)

    def toPython(self):
        return json.loads(Variant(self).__str__())

    def __del__(self):
        _sk._lib.sourcekitd_response_dispose(self)
