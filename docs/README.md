# Helix Documentation

Welcome to the Helix documentation. This directory contains guides for deploying, operating, and contributing to Helix.

## Documentation Version

**Current Version:** 1.4.0
**Last Updated:** January 2026
**Matches Release:** v1.4.0

> Documentation is versioned alongside the application. Always use documentation matching your Helix version.

---

## Quick Links

### Getting Started

- [Deployment Guide](deployment-guide.md) - Deploy Helix for a new client
- [Client Setup Checklist](client-setup-checklist.md) - Pre-deployment checklist

### Operations

- [Operations Runbook](operations-runbook.md) - Day-2 operations guide
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Deployment Verification](deployment-verification.md) - Post-deployment checks

### Usage

- [QA Import Guide](qa-import-guide.md) - Import knowledge base data

### Contributing

- [Contributing Guide](CONTRIBUTING.md) - How to contribute

---

## Documentation Structure

```
docs/
├── README.md                    # This file
├── CHANGELOG.md                 # Documentation changes
├── deployment-guide.md          # How to deploy
├── client-setup-checklist.md    # Pre-deployment checklist
├── operations-runbook.md        # Day-2 operations
├── troubleshooting.md           # Problem solving
├── deployment-verification.md   # Post-deployment checks
├── qa-import-guide.md           # Knowledge base import
├── CONTRIBUTING.md              # Contribution guide
└── images/                      # Screenshots and diagrams
```

---

## Version Compatibility

| Doc Version | Helix Version | Notes |
|-------------|---------------|-------|
| 1.4.0 | v1.4.0 | Current |
| 1.3.0 | v1.3.0 | Added demo auth |
| 1.2.0 | v1.2.0 | Added prompt versioning |
| 1.1.0 | v1.1.0 | Initial documentation |

---

## Finding Documentation for Your Version

Documentation is tagged with each release:

```bash
# View documentation for specific version
git checkout v1.3.0
cd docs/
```

Or browse on GitHub:
- Select your version tag
- Navigate to `/docs`

---

## Reporting Issues

Found an error in the documentation?

1. Check if already reported in GitHub Issues
2. Open new issue with:
   - Documentation file path
   - What's wrong
   - Suggested correction

---

*This documentation is maintained by the Helix team.*
