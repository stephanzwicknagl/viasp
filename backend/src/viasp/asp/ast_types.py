from clingo.ast import ASTType

SUPPORTED_TYPES = {
    ASTType.Comparison, ASTType.Aggregate, ASTType.Rule, ASTType.Program, ASTType.ShowSignature, ASTType.Definition,
    ASTType.Literal, ASTType.HeadAggregate, ASTType.HeadAggregateElement, ASTType.BodyAggregate, ASTType.Aggregate,
    ASTType.ConditionalLiteral, ASTType.Guard, ASTType.Comparison, ASTType.SymbolicAtom, ASTType.Function,
    ASTType.BodyAggregateElement, ASTType.BooleanConstant, ASTType.SymbolicAtom, ASTType.Variable, ASTType.SymbolicTerm,
    ASTType.Interval, ASTType.UnaryOperation, ASTType.BinaryOperation, ASTType.Defined, ASTType.External, ASTType.ProjectAtom, ASTType.ProjectSignature, ASTType.ShowTerm, ASTType.Minimize
}

UNSUPPORTED_TYPES = {
    ASTType.Disjunction,
}

def make_unknown_AST_enum_types():
    known = UNSUPPORTED_TYPES.union(SUPPORTED_TYPES)
    return set([e for e in ASTType if e not in known])


UNKNOWN_TYPES = make_unknown_AST_enum_types()
ARITH_TYPES = [ASTType.Comparison, ASTType.Aggregate]
