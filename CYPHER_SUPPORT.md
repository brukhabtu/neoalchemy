# NeoAlchemy Cypher Support Tracking

This file tracks Cypher features and their support status in NeoAlchemy's Pythonic query interface.

## Currently Unsupported Features

- **Complex Graph Patterns:** Defining multi-node/relationship patterns in `MATCH` clauses (e.g., `(p:Person)-[:WORKS_FOR]->(c:Company)`). Queries are limited to single nodes (`MATCH (e:Label)`).
- **`WITH` Clause:** Chaining query parts, aggregating, or filtering intermediate results.
- **`OPTIONAL MATCH`:** Matching patterns that might not exist.
- **Aggregation Functions:** Using functions like `avg()`, `sum()`, `collect()`, `min()`, `max()` in the `RETURN` clause (beyond the internal use of `count()`).
- **Map Projections:** Returning specific node/relationship properties (e.g., `RETURN e { .name, .age }`).
- **Path Queries:** Returning entire paths between nodes.
- **`UNWIND` Clause:** Expanding list values into individual rows.
- **Querying Relationship Properties:** Directly filtering or ordering based on properties of relationships in a `MATCH` pattern.
- **Advanced Functions:** Many built-in Cypher functions (e.g., spatial, temporal, advanced string manipulation).
