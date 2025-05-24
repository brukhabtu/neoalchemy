#!/bin/bash
set -e

echo "🚀 Setting up NeoAlchemy development environment..."

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
timeout=60
while ! python -c "
import sys
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password'))
    with driver.session() as session:
        session.run('RETURN 1')
    driver.close()
    print('✅ Neo4j connection successful')
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    sys.exit(1)
"; do
    sleep 2
    timeout=$((timeout - 2))
    if [ $timeout -le 0 ]; then
        echo "❌ Neo4j failed to start within 60 seconds"
        exit 1
    fi
done

# Initialize NeoAlchemy (auto-run initialize())
echo "🔧 Initializing NeoAlchemy..."
python -c "
from neoalchemy import initialize
initialize()
print('✅ NeoAlchemy initialized successfully')
"

# Run smoke tests to validate setup
echo "🧪 Running smoke tests..."
python -c "
# Test NeoAlchemy ORM
from neoalchemy.orm.models import Node
from neoalchemy.orm.repository import Neo4jRepository
from neo4j import GraphDatabase

class TestNode(Node):
    name: str

driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password'))
repo = Neo4jRepository(driver)

# Test basic ORM operations
try:
    with repo.transaction() as tx:
        test_node = TestNode(name='devcontainer_test')
        created = tx.create(test_node)
        found = tx.find_one(TestNode, name='devcontainer_test')
        tx.delete(found)
    print('✅ NeoAlchemy ORM working correctly')
except Exception as e:
    print(f'❌ NeoAlchemy ORM test failed: {e}')
    raise
finally:
    driver.close()
"

# Test MCP Server (basic import and setup)
echo "🤖 Testing MCP Server..."
python -c "
try:
    # Test that MCP server components can be imported
    import sys
    sys.path.append('/workspace/graph-mcp')
    
    # Basic import test
    from graph_mcp import mcp_server
    print('✅ MCP Server imports working correctly')
except Exception as e:
    print(f'⚠️  MCP Server test failed (may be expected): {e}')
    # Don't fail setup for MCP issues
"

# Create convenient aliases and shortcuts
echo "📝 Setting up development shortcuts..."
cat > /home/devuser/.bash_aliases << 'EOF'
# NeoAlchemy Development Aliases
alias test-unit='python -m pytest tests/unit/ -v'
alias test-integration='python -m pytest tests/e2e/ -v'  # Current e2e are actually integration
alias test-all='python -m pytest -v'
alias test-fast='python -m pytest tests/unit/ -q'

alias db-clear='python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver(\"bolt://neo4j:7687\", auth=(\"neo4j\", \"password\"))
with driver.session() as session:
    result = session.run(\"MATCH (n) DETACH DELETE n\")
    count = session.run(\"MATCH (n) RETURN count(n) as count\").single()[\"count\"]
    print(f\"Database cleared. Remaining nodes: {count}\")
driver.close()
"'

alias db-info='python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver(\"bolt://neo4j:7687\", auth=(\"neo4j\", \"password\"))
with driver.session() as session:
    nodes = session.run(\"MATCH (n) RETURN count(n) as count\").single()[\"count\"]
    rels = session.run(\"MATCH ()-[r]->() RETURN count(r) as count\").single()[\"count\"]
    print(f\"Database stats: {nodes} nodes, {rels} relationships\")
driver.close()
"'

alias lint='ruff check neoalchemy/'
alias format='ruff format neoalchemy/'
alias typecheck='mypy neoalchemy/'

# Quick development validation
alias dev-validate='echo "🔍 Validating development setup..." && python -c "
from neoalchemy import initialize
from neo4j import GraphDatabase
print(\"✅ NeoAlchemy imports working\")
driver = GraphDatabase.driver(\"bolt://neo4j:7687\", auth=(\"neo4j\", \"password\"))
with driver.session() as session:
    session.run(\"RETURN 1\")
print(\"✅ Neo4j connection working\")
driver.close()
print(\"✅ Development environment validated!\")
"'
EOF

echo "✅ Development environment setup complete!"
echo ""
echo "🎉 Ready to develop! Try these commands:"
echo "  dev-validate    - Validate everything is working"
echo "  test-fast       - Run quick unit tests"
echo "  test-all        - Run all tests"
echo "  db-info         - Show database stats"
echo "  db-clear        - Clear database"
echo "  lint            - Check code style"
echo ""
echo "🚀 Start coding with confidence!"