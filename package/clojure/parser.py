import sys
import re
from ..ply import yacc as yacc
from .lexer import ClojureLex

class ParserException(Exception):
    
    def __init__(self, *args, **kwargs):
        token = kwargs.pop("token", None)
        if token:
            self.line = token.lineno
            self.token = token.value
        super().__init__(*args, **kwargs)

    def __str__(self):
        if self.token:
            return "Syntax error '{token}', line {line}".format(
                token=self.token,
                line=self.line
            )
        else:
            return "Syntax error, EOF reached"

# BNF grammar for 'lisp'
# sexpr : atom
#       | readmacro sexpr
#       | keyword
#       | float
#       | integer
#       | list
#       | vector
#       | map
#       | nil
# sexprs : sexpr
#        | sexprs sexpr
# list : ( sexprs )
#      | ( )

_quiet = True

class LispLogger(yacc.PlyLogger):
    def debug(self, *args, **kwargs):
        if not _quiet:
            super(type(self), self).debug(*args, **kwargs)

def make_map(args):
    m = {}
    kvlist = [(args[i], args[i+1]) for i in range(0, len(args), 2)]
    for k, v in kvlist:
        m[k] = v
    return m

def quote_expr(raw):
    return ['quote', raw]

def deref_expr(raw):
    return ['deref', raw]

def init_type(raw):
    # Due to how python types are initialized, we can just treat them
    # as function calls.
    return raw

# Map from the regex that matches the atom to the function that takes
# in an ast, and modifies it as specified by the macro
READER_MACROS = {
    r'@': deref_expr,
    r'\'': quote_expr,
    r'\.': init_type,
    }

class ClojureParse(object):
    def build(self):
        return yacc.yacc(module=self, errorlog=LispLogger(sys.stderr))

    tokens = ClojureLex.tokens
    tokens.remove('NUMBER')
    tokens.extend(('FLOAT', 'INTEGER'))

    def p_sexpr_nil(self, p):
        'sexpr : NIL'
        p[0] = None

    def p_sexpr_atom(self, p):
        'sexpr : ATOM'
        p[0] = p[1]

    def p_sexpr_quoted(self, p):
        'sexpr : QUOTED'
        p[0] = p[1][1:-1]

    def p_sexpr_readmacro(self, p):
        'sexpr : READMACRO sexpr'
        for regex, func in READER_MACROS.items():
            if re.match(regex, p[1]):
                p[0] = func(p[2])
                return

    def p_keyword(self, p):
        'sexpr : KEYWORD'
        p[0] = p[1]

    def p_sexpr_float(self, p):
        'sexpr : FLOAT'
        p[0] = float(p[1])

    def p_sexpr_integer(self, p):
        'sexpr : INTEGER'
        p[0] = int(p[1])

    def p_sexpr_seq(self, p):
        '''
        sexpr : list
              | vector
              | map
        '''
        p[0] = p[1]

    def p_sexprs_sexpr(self, p):
        'sexprs : sexpr'
        p[0] = p[1]

    def p_sexprs_sexprs_sexpr(self, p):
        'sexprs : sexprs sexpr'
        if type(p[1]) is list:
            p[0] = p[1]
            p[0].append(p[2])
        else:
            p[0] = [p[1], p[2]]

    def p_list(self, p):
        'list : LPAREN sexprs RPAREN'
        p[0] = tuple(p[2])

    def p_empty_list(self, p):
        'list : LPAREN RPAREN'
        p[0] = tuple()

    def p_vector(self, p):
        'vector : LBRACKET sexprs RBRACKET'
        if not isinstance(p[2], list):
            p[0] = [p[2]]
        else:
            p[0] = p[2]

    def p_empty_vector(self, p):
        'vector : LBRACKET RBRACKET'
        p[0] = []

    def p_map(self, p):
        'map : LBRACE sexprs RBRACE'
        p[0] = make_map(p[2])

    def p_empty_map(self, p):
        'map : LBRACE RBRACE'
        p[0] = {}

    def p_error(self, p):
        if p:
            raise ParserException(token=p)
        else:
            raise ParserException()
