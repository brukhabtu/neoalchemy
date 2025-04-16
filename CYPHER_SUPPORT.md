# Cypher Expression System Architecture

## Separation of Concerns

The NeoAlchemy expression system follows a clean separation of concerns pattern to ensure maintainability and extensibility:

1. **Expression Layer**: Provides Pythonic interface for building queries
   - Focused on user-friendly syntax (e.g., `Person.age > 30`)
   - Handles operator overloading and special methods (e.g., `__eq__`, `__in__`)
   - Manages expression state for complex operations
   - **Does not** contain Cypher-specific implementation details

2. **Adapter Layer**: Translates expressions to Cypher elements
   - Implements the adapter pattern to decouple expression and Cypher layers
   - Centralizes all conversion logic in one place
   - Handles entity variable assignment and management
   - Provides extension points for alternative query language support

3. **Cypher Layer**: Generates Cypher query strings and parameters
   - Implements the specific syntax of the Cypher query language
   - Handles property references, query builders, and clauses
   - Manages parameter generation and replacement
   - **Does not** directly interact with the expression layer

## Expression Adapter Pattern

The expression adapter pattern provides several benefits:

1. **Decoupling**: Expressions don't directly depend on Cypher implementation details
2. **Configurability**: Entity variables can be configured through the adapter
3. **Extensibility**: New query languages could be supported by creating new adapters
4. **Centralization**: Conversion logic is centralized in one place
5. **Testability**: Components can be tested in isolation

### Implementation

```python
# Expression layer - no Cypher knowledge
class FieldExpr(Expr):
    """Field expression for referencing model fields."""
    
    def __init__(self, name: str):
        self.name = name
    
    def __eq__(self, other: Any) -> Expr:
        """Equality comparison."""
        return OperatorExpr(self.name, "=", other)

# Adapter layer - knows both domains
class ExpressionAdapter:
    """Adapter for converting expressions to cypher elements."""
    
    def __init__(self, entity_var: str = 'e'):
        """Initialize the adapter."""
        self.entity_var = entity_var
    
    def to_cypher_element(self, expr: Expr) -> CypherElement:
        """Convert an expression to a cypher element."""
        if isinstance(expr, FieldExpr):
            return PropertyRef(self.entity_var, expr.name)
        # ...other conversions

# Cypher layer - no expression knowledge
class PropertyRef(CypherElement):
    """Reference to a property in Cypher."""
    
    def __init__(self, entity: str, property_name: str):
        self.entity = entity
        self.property_name = property_name
    
    def to_cypher(self) -> str:
        """Convert to Cypher syntax."""
        return f"{self.entity}.{self.property_name}"
```

## Usage in Query Builder

```python
# Configure the adapter when creating a query builder
def __init__(self, repo: Any, model_class: Type[M], entity_var: str = 'e'):
    self.entity_var = entity_var
    
    # Configure the expression adapter to use our entity variable
    from neoalchemy.core.expressions import Expr, ExpressionAdapter
    Expr.set_adapter(ExpressionAdapter(entity_var=self.entity_var))
```