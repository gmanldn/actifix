# Actifix Documentation Index

Welcome to the Actifix documentation! This index provides a comprehensive guide to all available documentation, organized by purpose and audience.

## Quick Start

- **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation guide
- **[README.md](../README.md)** - Project overview and basic usage

## User Documentation

### Getting Started
- **[FRAMEWORK_OVERVIEW.md](FRAMEWORK_OVERVIEW.md)** - Complete framework overview
- **[QUICKSTART.md](QUICKSTART.md)** - Rapid setup guide
- **[INSTALLATION.md](INSTALLATION.md)** - Installation instructions

### Usage Guides
- **[src/actifix/README.md](../src/actifix/README.md)** - API reference and usage examples
- **[actifix-frontend/README.md](../actifix-frontend/README.md)** - Web interface documentation

## Developer Documentation

### Development Workflow
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development guide and standards
- **[QUICKDEV.md](QUICKDEV.md)** - Fast development workflow for AI agents
- **[AGENTS.md](../AGENTS.md)** - Agent instructions and mandatory rules

### Architecture Documentation
- **[architecture/ARCHITECTURE_CORE.md](architecture/ARCHITECTURE_CORE.md)** - Core architectural principles
- **[architecture/MODULES.md](architecture/MODULES.md)** - Module catalog and dependencies
- **[architecture/MAP.yaml](architecture/MAP.yaml)** - Canonical architecture map
- **[architecture/DEPGRAPH.json](architecture/DEPGRAPH.json)** - Dependency graph

### Testing & Quality
- **[TESTING.md](TESTING.md)** - Testing strategy and guidelines *(Coming Soon)*
- **Test Coverage Reports** - Available after running `python test.py --coverage`

## Reference Documentation

### Release Information
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and release notes
- **[LICENSE](../LICENSE)** - MIT License terms

### Configuration
- **Environment Variables** - See [INSTALLATION.md](INSTALLATION.md#environment-variables)
- **Configuration Files** - See [DEVELOPMENT.md](DEVELOPMENT.md#configuration)

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions *(Coming Soon)*
- **[MONITORING.md](MONITORING.md)** - Operational monitoring guide *(Coming Soon)*

## Architecture Overview

```
docs/
├── INDEX.md                    # This file - documentation catalog
├── QUICKSTART.md              # 5-minute setup guide
├── INSTALLATION.md            # Detailed installation
├── DEVELOPMENT.md             # Development workflow
├── FRAMEWORK_OVERVIEW.md      # Complete framework overview
├── QUICKDEV.md               # Fast development for AI agents
├── ultrathink_tickets_summary.md  # Architecture tickets summary
└── architecture/             # Architecture documentation
    ├── ARCHITECTURE_CORE.md  # Core principles
    ├── MODULES.md            # Module catalog
    ├── MAP.yaml              # Architecture map
    └── DEPGRAPH.json         # Dependency graph
```

## Documentation Standards

All documentation follows these principles:

1. **Purpose-Driven** - Each document clearly states its purpose and scope
2. **Audience-Specific** - Content tailored for users, developers, or operators
3. **Actionable** - Includes concrete steps and examples
4. **Current** - Kept up-to-date with code changes
5. **Cross-Referenced** - Links to related documentation

## Contributing to Documentation

When adding or updating documentation:

1. **Follow the template** - Use existing docs as templates
2. **Update this index** - Add new documents to the appropriate section
3. **Cross-reference** - Link to related documentation
4. **Test examples** - Ensure all code examples work
5. **Review for clarity** - Have someone else review for clarity

## Documentation Maintenance

- **Freshness**: Architecture docs auto-generated every 7 days
- **Validation**: Documentation links checked in CI
- **Reviews**: All doc changes require review
- **Versioning**: Major changes documented in CHANGELOG.md

## Getting Help

If you can't find what you're looking for:

1. **Search this index** - Use Ctrl+F to find relevant sections
2. **Check the architecture docs** - For technical implementation details
3. **Review the code** - Source code in `src/actifix/` is well-documented
4. **Ask questions** - Open an issue on GitHub

## Document Status Legend

- ✅ **Complete** - Comprehensive and current
- 🚧 **In Progress** - Being actively developed
- 📋 **Planned** - Scheduled for creation
- ⚠️ **Needs Update** - Exists but may be outdated

### Current Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| QUICKSTART.md | ✅ Complete | 2026-01-11 |
| INSTALLATION.md | ✅ Complete | 2026-01-11 |
| DEVELOPMENT.md | ✅ Complete | 2026-01-11 |
| FRAMEWORK_OVERVIEW.md | ✅ Complete | 2026-01-11 |
| QUICKDEV.md | ✅ Complete | 2026-01-11 |
| architecture/ARCHITECTURE_CORE.md | ✅ Complete | 2026-01-10 |
| architecture/MODULES.md | ✅ Complete | 2026-01-10 |
| TESTING.md | 📋 Planned | - |
| MONITORING.md | 📋 Planned | - |
| TROUBLESHOOTING.md | 📋 Planned | - |

---

**Last Updated**: 2026-01-11  
**Maintained By**: Actifix Team  
**Review Cycle**: Monthly
