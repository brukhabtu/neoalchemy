# Known Issues and Future Improvements

## Type Checking Warnings

### Operator Overloading Type Warnings

These warnings can be safely ignored as they're related to operator overloading in the expression system. Python's type system doesn't handle operator overloading returns well in the abstract case.

- `Return type "LogicalExpr" of "__eq__" incompatible with return type "bool" in supertype "object"`
- `Return type "FunctionComparisonExpr" of "__eq__" incompatible with return type "bool" in supertype "object"`
- `Unsupported left operand type for & ("Expr")`

The expressions system uses operator overloading to provide an intuitive query building API. While these operations technically return expression objects (not booleans), this is a common pattern for fluent interfaces and DSLs.

### Core Cypher Query Type Error

- `Incompatible return value type (got "tuple[str, dict[str, Any]]", expected "tuple[str, int]")` 

This error in `neoalchemy/core/cypher/query.py` line 108 is related to the return type signature being incorrect. The function returns a Cypher query string and a parameters dictionary, but the type annotation indicates it returns a string and an integer.

## Neo4j Driver Deprecation Warnings

- `Importing Config from neo4j is deprecated without replacement. It's internal and will be removed in a future version.`
- `GqlStatusObject is part of GQLSTATUS support, which is a preview feature.`
- `NotificationClassification is part of GQLSTATUS support, which is a preview feature.`
- `NotificationDisabledClassification is part of GQLSTATUS support, which is a preview feature.`
- `Importing PoolConfig from neo4j is deprecated without replacement.`
- `Importing SessionConfig from neo4j is deprecated without replacement.`
- `SummaryNotificationPosition is deprecated. Use SummaryInputPosition instead.`
- `Importing WorkspaceConfig from neo4j is deprecated without replacement.`
- `Importing log from neo4j is deprecated without replacement.`

These warnings are from the Neo4j driver and involve internal details that should not be used directly. The warnings appear during inspection of modules and don't affect functionality.

## Pydantic Warnings

- `Field name "id" in "TestModel" shadows an attribute in parent "Neo4jModel"`
- `PydanticSerializationUnexpectedValue(Expected \`datetime\` - serialized value may not be as expected [input_value=<FieldExpr object>, input_type=FieldExpr])`

These are from the Pydantic library and relate to field inheritance and serialization of expression objects.

## Recommended Fixes for Future Development

1. Fix the return type annotation in `cypher/query.py` to match the actual return value
2. Add type ignore comments for operator overloading issues
3. Update test fixtures to avoid Neo4j driver deprecation warnings
4. Add custom serializers for FieldExpr to improve Pydantic serialization
5. Consider using Protocol classes to better represent the expression system's type behavior

## Notes on Python 3.12 Support

The code runs on Python 3.12 but generates numerous deprecation warnings. Future development should:

1. Update typing imports to use the newer style (import directly from typing)
2. Use PEP 695 type alias syntax for cleaner typing
3. Add type checker config file (pyproject.toml) to suppress specific known warnings