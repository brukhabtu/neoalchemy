# GitHub Workflows

This directory contains CI/CD workflows for NeoAlchemy.

## Workflows

### 🧪 `unit-tests.yml`
**Purpose**: Fast unit tests in Docker containers
- Builds Docker image with all dependencies
- Runs isolated unit tests (no database required)
- Pushes image to GitHub Container Registry
- **Triggers**: Push to main/develop, PRs
- **Image naming**: Based on branch/tag name

### 🔧 `integration-tests.yml`
**Purpose**: Integration tests with real Neo4j database
- Spins up Neo4j service container
- Runs full integration test suite
- Tests real database interactions
- **Triggers**: Push to main/develop, PRs

### 🚀 `ci.yml` (Comprehensive)
**Purpose**: Complete CI pipeline with all checks
- **Unit Tests**: Fast Docker-based isolated tests
- **Code Quality**: Linting, type checking, formatting
- **Integration Tests**: Full database integration
- **Performance Verification**: Ensures unit tests run <1 second
- **Image Publishing**: Pushes to GitHub Container Registry
- **Triggers**: Push to main/develop, PRs

## Docker Images

Images are published to GitHub Container Registry:
- `ghcr.io/[owner]/[repo]:main` - Latest from main branch
- `ghcr.io/[owner]/[repo]:develop` - Latest from develop branch  
- `ghcr.io/[owner]/[repo]:pr-123` - Pull request builds
- `ghcr.io/[owner]/[repo]:sha-abcd123` - Commit-specific builds

## Usage Examples

### Running Unit Tests Locally
```bash
# Build and run unit tests
docker build -t neoalchemy-unit-tests .
docker run --rm neoalchemy-unit-tests

# Or use the published image
docker run --rm ghcr.io/[owner]/neoalchemy:main
```

### Performance Requirements
- Unit tests must complete in <1 second total
- Unit tests must not require database connectivity
- All tests must pass for CI to succeed

## Status Badges

Add these to your README:
```markdown
![Unit Tests](https://github.com/[owner]/neoalchemy/workflows/Unit%20Tests/badge.svg)
![Integration Tests](https://github.com/[owner]/neoalchemy/workflows/Integration%20Tests/badge.svg)
![CI](https://github.com/[owner]/neoalchemy/workflows/Continuous%20Integration/badge.svg)
```