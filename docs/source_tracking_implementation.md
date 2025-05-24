# Source Tracking Implementation in NeoAlchemy

This document explains the technical implementation of source tracking in NeoAlchemy, providing insights for anyone looking to extend or modify the system.

## Architecture

The source tracking system follows these design principles:

1. **Minimal Intrusion**: Source tracking is built into the base models but doesn't require any changes to existing model definitions
2. **Automatic Management**: Source nodes and relationships are created and maintained automatically 
3. **Easy Querying**: The system provides simple methods for querying entities by their sources

## Components

### 1. Source and SOURCED_FROM Models

The core models are defined in `neoalchemy/orm/tracking/sources.py`:

- `SourceScheme`: An enumeration of supported URI schemes (`jira`, `confluence`, `llm`, etc.)
- `Source`: A Node model representing a data source with properties like `uri`, `scheme`, `identifier`, etc.
- `SOURCED_FROM`: A Relationship model connecting entities to their sources

### 2. Base Model Integration

All Neo4j models in NeoAlchemy (`Node` and `Relationship`) include:

- A `sources: List[str]` field for storing source URIs
- Validation for the source URI format

### 3. Repository Methods

The `Neo4jTransaction` class in `neoalchemy/orm/repository.py` is extended with methods for:

- `create_source_from_uri`: Create a Source node from a URI string
- `relate_to_source`: Connect an entity to a source
- `relate_to_sources`: Connect an entity to multiple sources
- `get_sources`: Get all sources for an entity
- `find_by_source`: Find entities by source URI
- `find_by_source_scheme`: Find entities by source scheme

## Implementation Details

### Automatic Source Handling

When creating an entity with source URIs:

```python
john = Person(
    name="John Doe",
    email="john.doe@example.com",
    sources=["jira:HR-123", "llm:claude-3"]
)
created_john = tx.create(john)
```

The `create` method in `Neo4jTransaction` processes the sources:

1. The entity is created in the database
2. If the entity has source URIs, `relate_to_sources` is called
3. For each source URI:
   - The URI is validated
   - Source nodes are created if they don't exist
   - SOURCED_FROM relationships are created

This is implemented in the `create` method:

```python
def create(self, model: M) -> M:
    # ... create entity logic ...
    
    # Save source URIs for later use
    source_uris = data.get("sources", [])
    
    # ... node creation logic ...
    
    # Create source relationships automatically if we have valid source URIs
    if hasattr(model, "sources") and source_uris:
        self.relate_to_sources(created_model)
    
    return created_model
```

### URI Parsing and Validation

The `Source.parse_uri` method breaks down a URI into its components:

```python
@staticmethod
def parse_uri(uri: str) -> tuple[str, str, SourceScheme]:
    """Parse a source URI into its components."""
    if ":" not in uri:
        raise ValueError(f"Invalid source URI format: {uri}. Expected format: scheme:identifier")
        
    scheme, identifier = uri.split(":", 1)
    
    # Try to map to known scheme, fallback to CUSTOM
    try:
        scheme_enum = SourceScheme(scheme)
    except ValueError:
        scheme_enum = SourceScheme.CUSTOM
        
    return uri, identifier, scheme_enum
```

### Source Creation

The `Source.from_uri` method creates a Source object from a URI:

```python
@classmethod
def from_uri(cls, uri: str, name: Optional[str] = None, **kwargs) -> "Source":
    """Create a Source from a URI string."""
    uri, identifier, scheme_enum = cls.parse_uri(uri)
    
    # Generate a default name if not provided
    if name is None:
        scheme_str = scheme_enum.value if scheme_enum != SourceScheme.CUSTOM else uri.split(":", 1)[0]
        name = f"{scheme_str.title()} {identifier}"
        
    return cls(
        uri=uri,
        scheme=scheme_enum,
        identifier=identifier,
        name=name,
        **kwargs
    )
```

### Query Methods

The `find_by_source` method in `Neo4jTransaction` finds entities connected to a specific source:

```python
def find_by_source(self, model_class: Type[M], source_uri: str) -> List[M]:
    """Find all entities of a given type connected to a specific source."""
    node_label = getattr(model_class, "__label__", model_class.__name__)
    
    query = f"""
    MATCH (e:{node_label})-[r:SOURCED_FROM]->(s:Source)
    WHERE s.uri = $source_uri
    RETURN e
    """
    
    result = self._tx.run(query, {"source_uri": source_uri})
    
    entities = []
    for record in result:
        entity_data = dict(record["e"])
        entities.append(model_class(**entity_data))
        
    return entities
```

## Extension Points

If you want to extend the source tracking system, consider these points:

### 1. Custom Source Types

You can add custom source types by extending the `SourceScheme` enum:

```python
class MySourceScheme(SourceScheme):
    """Extended source scheme types."""
    INTERNAL_DB = "internal_db"
    LEGACY_SYSTEM = "legacy"
    THIRD_PARTY = "third_party"
```

### 2. Enhanced SOURCED_FROM Relationship

You can create a custom SOURCED_FROM relationship with additional fields:

```python
class EnhancedSOURCED_FROM(SOURCED_FROM):
    """Enhanced relationship with confidence score and other metadata."""
    confidence: float = Field(default=1.0)
    method: Optional[str] = Field(default=None)
    primary: bool = Field(default=False)
```

### 3. Custom Repository Methods

You can extend the repository with custom source-related methods:

```python
def get_primary_sources(self, entity: Any) -> List[Source]:
    """Get primary sources for an entity."""
    # Implementation here
```

## Performance Considerations

The source tracking system is designed to be efficient, but consider these tips for performance optimization:

1. **Batch Source Creation**: When importing large amounts of data, consider creating Source nodes in batches first.

2. **URI Reuse**: Reuse the same source URIs for related entities to minimize the number of Source nodes.

3. **Index Usage**: The system automatically creates indexes on `Source.uri` and `Source.scheme`, which helps with query performance.

4. **Query Patterns**: When searching for entities by source, use the provided methods which leverage these indexes.

## Advanced Query Patterns

Some advanced query patterns possible with the source tracking system:

```cypher
// Find entities with sources from multiple schemes
MATCH (e:Person)-[:SOURCED_FROM]->(s1:Source)
WHERE s1.scheme = 'jira'
MATCH (e)-[:SOURCED_FROM]->(s2:Source)
WHERE s2.scheme = 'slack'
RETURN e

// Find entities with conflicting sources
MATCH (e:Person)-[r1:SOURCED_FROM]->(s1:Source)
MATCH (e)-[r2:SOURCED_FROM]->(s2:Source)
WHERE s1.scheme = s2.scheme AND s1.uri <> s2.uri
RETURN e, s1, s2

// Find most referenced sources
MATCH (s:Source)<-[r:SOURCED_FROM]-()
RETURN s.uri, count(r) as usage
ORDER BY usage DESC
LIMIT 10
```

These can be implemented as repository methods if commonly needed.

## Integration with Validation

The source tracking system integrates with Pydantic validation:

```python
# Add a model validator to require sources
@model_validator(mode="after")
def validate_has_sources(self):
    """Validate that the model has at least one source."""
    if not getattr(self, "sources", None):
        raise ValueError(f"{self.__class__.__name__} requires at least one source")
    return self
```

## Migration from Custom Systems

When migrating from a custom source tracking system to NeoAlchemy's built-in one:

1. Map your existing source identifiers to the URI format (`scheme:identifier`)
2. Use the built-in `sources` field instead of custom fields
3. Use repository methods like `relate_to_source` and `find_by_source` instead of custom queries
4. Consider writing a migration script to convert existing data to the new format