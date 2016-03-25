import re
placeholderRegex = re.compile(r"<#T##([^#]*)(##.*)*#>")


def fromXcodePlaceholder(placeholder):
    """Converts SK-style completions to ST-style completions.
    input like ".append(<#T##other: String##String#>)"
    output     ".append(${0:other:String})"

    """
    i = 0
    while True:
        match = placeholderRegex.search(placeholder)
        if not match: break
        newstr = "${%d:%s}" % (i, match.group(1))
        placeholder = placeholder[:match.start()] + newstr + placeholder[match.end():]
        i += 1
    return placeholder

def shortType(tipe):
    #SwiftLangSupport.cpp
    tipes = {"source.lang.swift.decl.function.free":"func",
            "source.lang.swift.ref.function.free":"func",
            "source.lang.swift.decl.function.method.instance":"method",
            "source.lang.swift.ref.function.method.instance":"method",
            "source.lang.swift.decl.function.method.static":"static method",
            "source.lang.swift.ref.function.method.static":"static method",
            "source.lang.swift.decl.function.method.class":"class method",
            "source.lang.swift.ref.function.method.class":"class method",
            "source.lang.swift.decl.function.accessor.getter":"get",
            "source.lang.swift.ref.function.accessor.getter":"get",
            "source.lang.swift.decl.function.accessor.setter":"set",
            "source.lang.swift.ref.function.accessor.setter":"set",
            "source.lang.swift.decl.function.accessor.willset":"willSet",
            "source.lang.swift.ref.function.accessor.willset":"willSet",
            "source.lang.swift.decl.function.accessor.didset":"didSet",
            "source.lang.swift.ref.function.accessor.didset":"didSet",
            "source.lang.swift.decl.function.accessor.address":"address",
            "source.lang.swift.ref.function.accessor.address":"address",
            "source.lang.swift.decl.function.accessor.mutableaddress":"mutable address",
            "source.lang.swift.ref.function.accessor.mutableaddress":"mutable address",
            "source.lang.swift.decl.function.constructor":"init",
            "source.lang.swift.ref.function.constructor":"init",
            "source.lang.swift.decl.function.destructor":"deinit",
            "source.lang.swift.ref.function.destructor":"deinit",
            "source.lang.swift.decl.function.operator.prefix":"++operator",
            "source.lang.swift.ref.function.operator.prefix":"++operator",
            "source.lang.swift.decl.function.operator.postfix":"operator++",
            "source.lang.swift.ref.function.operator.postfix":"operator++",
            "source.lang.swift.decl.function.operator.infix":"oper+ator",
            "source.lang.swift.ref.function.operator.infix":"oper+ator",
            "source.lang.swift.decl.function.subscript":"[]",
            "source.lang.swift.ref.function.subscript":"[]",
            "source.lang.swift.decl.var.global":"global var",
            "source.lang.swift.ref.var.global":"global var",
            "source.lang.swift.decl.var.instance":"ivar",
            "source.lang.swift.ref.var.instance":"ivar",
            "source.lang.swift.decl.var.static":"static var",
            "source.lang.swift.ref.var.static":"static var",
            "source.lang.swift.decl.var.class":"class var",
            "source.lang.swift.ref.var.class":"class var",
            "source.lang.swift.decl.var.local":"local var",
            "source.lang.swift.ref.var.local":"local var",
            "source.lang.swift.decl.var.parameter":"var parameter", # what the hell is this?
            "source.lang.swift.decl.module":"module",
            "source.lang.swift.decl.class":"class",
            "source.lang.swift.ref.class":"class",
            "source.lang.swift.decl.struct":"struct",
            "source.lang.swift.ref.struct":"struct",
            "source.lang.swift.decl.enum":"enum",
            "source.lang.swift.ref.enum":"enum",
            "source.lang.swift.decl.enumcase":"case",
            "source.lang.swift.decl.enumelement":"element",
            "source.lang.swift.ref.enumelement":"element",
            "source.lang.swift.decl.protocol":"protocol",
            "source.lang.swift.ref.protocol":"protocol",
            "source.lang.swift.decl.extension":"extension",
            "source.lang.swift.decl.extension.struct":"extension",
            "source.lang.swift.decl.extension.class":"extension",
            "source.lang.swift.decl.extension.enum":"extension",
            "source.lang.swift.decl.extension.protocol":"extension",
            "source.lang.swift.decl.associatedtype":"associatedtype",
            "source.lang.swift.ref.associatedtype":"associatedtype",
            "source.lang.swift.decl.typealias":"typealias",
            "source.lang.swift.ref.typealias":"typealias",
            "source.lang.swift.decl.generic_type_param":"<Generic>",
            "source.lang.swift.ref.generic_type_param":"<Generic>",
            "source.lang.swift.ref.module":"module",
            "source.lang.swift.stmt.foreach":"statement",
            "source.lang.swift.stmt.for":"statement",
            "source.lang.swift.stmt.while":"statement",
            "source.lang.swift.stmt.repeatwhile":"statement",
            "source.lang.swift.stmt.if":"statement",
            "source.lang.swift.stmt.guard":"statement",
            "source.lang.swift.stmt.switch":"statement",
            "source.lang.swift.stmt.case":"statement",
            "source.lang.swift.stmt.brace":"}",
            "source.lang.swift.expr.call":"()",
            "source.lang.swift.expr.array":"[]",
            "source.lang.swift.expr.dictionary":"[:]",
            "source.lang.swift.expr.object_literal":"literal",
            "source.lang.swift.structure.elem.id":"elem.id",
            "source.lang.swift.structure.elem.expr":"elem.expr",
            "source.lang.swift.structure.elem.init_expr":"elem.init_expr",
            "source.lang.swift.structure.elem.condition_expr":"elem.condition_expr",
            "source.lang.swift.structure.elem.pattern":"elem.pattern",
            "source.lang.swift.structure.elem.typeref":"elem.typeref",
            "source.lang.swift.syntaxtype.keyword":"keyword",
            "source.lang.swift.syntaxtype.identifier":"identifier",
            "source.lang.swift.syntaxtype.typeidentifier":"type identifier",
            "source.lang.swift.syntaxtype.buildconfig.keyword":"build config keyword",
            "source.lang.swift.syntaxtype.buildconfig.id":"build config id",
            "source.lang.swift.syntaxtype.attribute.id":"attribute id",
            "source.lang.swift.syntaxtype.attribute.builtin":"attribute builtin",
            "source.lang.swift.syntaxtype.number":"42",
            "source.lang.swift.syntaxtype.string":'"string"',
            "source.lang.swift.syntaxtype.string_interpolation_anchor":"string interpolation anchor", # wtf?
            "source.lang.swift.syntaxtype.comment": "//",
            "source.lang.swift.syntaxtype.doccomment": "///",
            "source.lang.swift.syntaxtype.doccomment.field":"///",
            "source.lang.swift.syntaxtype.comment.mark":"//",
            "source.lang.swift.syntaxtype.comment.url":"http://",
            "source.lang.swift.syntaxtype.placeholder":"placeholder",
            "source.lang.swift.syntaxtype.objectliteral":"object",

            #SwiftCompletion.cpp
            "source.lang.swift.keyword":"keyword",
            "source.lang.swift.keyword.let":"keyword",
            "source.lang.swift.keyword.var":"keyword",
            "source.lang.swift.keyword.if":"keyword",
            "source.lang.swift.keyword.for":"keyword",
            "source.lang.swift.keyword.while":"keyword",
            "source.lang.swift.keyword.func":"keyword",
            "source.lang.swift.pattern":"pattern"
    }
    return tipes[tipe] 