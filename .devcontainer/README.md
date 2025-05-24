# NeoAlchemy Devcontainer

This devcontainer provides a **complete, ready-to-go development environment** for both NeoAlchemy ORM and MCP Server development.

## 🚀 **Instant Setup**

1. **Open in VS Code with Dev Containers extension**
2. **Choose "Reopen in Container"** 
3. **Wait for setup to complete** (automatic)
4. **Start coding!** ✨

## 🎯 **What You Get Out of the Box**

### **Fully Configured Environment**
- ✅ Python 3.13 with uv package manager
- ✅ All dependencies pre-installed
- ✅ Neo4j 4.4 running and accessible
- ✅ NeoAlchemy initialized and tested
- ✅ MCP Server components ready
- ✅ VS Code extensions and settings optimized

### **Pre-configured Services**
- **Neo4j Database**: `bolt://neo4j:7687` (auto-started)
- **Neo4j Browser**: `http://localhost:7474` (forwarded)
- **Development aliases**: Ready-to-use commands

### **Development Commands**
```bash
# Quick validation
dev-validate      # Check everything works

# Testing (fast to slow)
test-fast         # Unit tests only (<1s)
test-unit         # All unit tests
test-integration  # Integration tests with DB
test-all          # Everything

# Database utilities
db-info           # Show database stats  
db-clear          # Clear all data

# Code quality
lint              # Check code style
format            # Auto-format code
typecheck         # Run mypy
```

## 🧪 **Testing Strategy**

The devcontainer supports the dual-component testing approach:

### **Unit Tests** (No Database)
```bash
test-unit
# Tests both NeoAlchemy ORM and MCP Server logic
# Runs in <1 second
```

### **Integration Tests** (Real Database)  
```bash
test-integration  
# Tests database operations for both components
# Runs in ~5 seconds
```

### **Cross-Component Tests**
```bash
test-all
# Includes tests of MCP Server using NeoAlchemy ORM
# Full validation of both components working together
```

## 🔧 **Architecture**

```
Services:
├── devcontainer (Python 3.13 + dependencies)
├── neo4j (Database service)  
└── traefik (Reverse proxy)

Components Tested:
├── neoalchemy/ (ORM)
├── graph-mcp/ (MCP Server)
└── Cross-component integration
```

## 🎯 **First Steps After Setup**

1. **Validate environment**: `dev-validate`
2. **Run quick tests**: `test-fast` 
3. **Explore the code**: Both `neoalchemy/` and `graph-mcp/`
4. **Make changes and test**: `test-unit` after each change

## 🐛 **Troubleshooting**

### Container Won't Start
```bash
# Rebuild container
Ctrl+Shift+P -> "Dev Containers: Rebuild Container"
```

### Database Issues
```bash
# Check database
db-info

# Reset database  
db-clear

# Validate connection
dev-validate
```

### Test Failures
```bash
# Run specific test
python -m pytest tests/unit/test_models.py -v

# Check database state
db-info
```

## ⚡ **Performance Expectations**

- **Container startup**: ~2 minutes (first time)
- **Subsequent starts**: ~30 seconds  
- **Unit tests**: <1 second
- **Integration tests**: <10 seconds
- **All tests**: <30 seconds

The devcontainer is optimized for **fast iteration cycles** and **reliable testing**.