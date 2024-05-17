from clingo.ast import ASTType

UNSUPPORTED_TYPES = {
    ASTType.Disjunction,
}

def make_supported_AST_enum_types():
    unsupported = UNSUPPORTED_TYPES
    return set([e for e in ASTType if e not in unsupported])


SUPPORTED_TYPES = make_supported_AST_enum_types()

ARITH_TYPES = {
    ASTType.Comparison, ASTType.Aggregate
}
