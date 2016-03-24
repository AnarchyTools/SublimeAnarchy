import ply.lex as lex

class LexerException(Exception):
    
    def __init__(self, *args, **kwargs):
        token = kwargs.pop("token")
        self.line = token.lexer.lineno
        self.column = (token.lexpos - token.lexer.last_cr) + 1
        self.character = token.value[0]
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "Illegal character '{char}', line {line}, column {col}".format(
            char=self.character,
            line=self.line,
            col=self.column
        )


class ClojureLex(object):
    def build(self,**kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        return self.lexer

    reserved = {'nil': 'NIL'}

    tokens = ['ATOM', 'KEYWORD',
              'NUMBER', 'READMACRO',
              'LBRACKET', 'RBRACKET',
              'LBRACE', 'RBRACE',
              'LPAREN', 'RPAREN',
              'QUOTED'] + list(reserved.values())

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_QUOTED = r'"[^"]*"' # FIXME: what with escaped quotes?
    t_ignore = ' ,\t\r'
    t_ignore_COMMENT = r'\;.*'

    def t_KEYWORD(self, t):
        r'\:[a-zA-Z_-]+'
        t.value = t.value[1:]
        return t

    def t_NUMBER(self, t):
        r'[+-]?((\d+(\.\d+)?([eE][+-]?\d+)?)|(\.\d+([eE][+-]?\d+)?))'
        val = t.value
        if '.' in val or 'e' in val.lower():
            t.type = 'FLOAT'
        else:
            t.type = 'INTEGER'
        return t

    def t_ATOM(self, t):
        r'[\*\+\!\-\_a-zA-Z_-]+'
        t.type = self.reserved.get(t.value, 'ATOM')
        return t

    def t_READMACRO(self, t):
        r'[@\'#^`\\.]+'
        # All the possible reader macro chars
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        t.lexer.last_cr = t.lexer.lexpos

    def t_error(self, t):
        t.lexer.skip(1)
        raise LexerException(token=t)
