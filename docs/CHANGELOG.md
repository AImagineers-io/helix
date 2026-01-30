# Documentation Changelog

All notable changes to Helix documentation are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.4.0] - 2026-01-30

### Added

- **Operations Runbook** (`operations-runbook.md`)
  - Backup procedures for PostgreSQL and Redis
  - Log access and rotation
  - Scaling guidelines
  - Container management
  - Incident response procedures

- **Troubleshooting Guide** (`troubleshooting.md`)
  - Chat not responding diagnosis
  - Embeddings not generating fixes
  - Facebook webhook debugging
  - Admin UI issues
  - Database troubleshooting

- **Deployment Verification** (`deployment-verification.md`)
  - Post-deployment checklist
  - Automated verification script
  - Rollback criteria

- **QA Import Guide** (`qa-import-guide.md`)
  - CSV, JSON, and text format specifications
  - Validation rules
  - Common import errors and solutions
  - Sample files

- **Contributing Guide** (`CONTRIBUTING.md`)
  - Code contribution workflow
  - Documentation update process
  - Screenshot maintenance procedures

- **Screenshot Capture Script** (`scripts/capture_screenshots.sh`)
  - Automated screenshot capture with Playwright
  - Consistent viewport and settings

- **Documentation Versioning**
  - Version tracking in README.md
  - CHANGELOG.md for documentation changes

### Changed

- Updated deployment guide with environment safety checks
- Added demo authentication configuration

---

## [1.3.0] - 2026-01-25

### Added

- Demo environment configuration (`.env.demo`)
- Environment safety documentation

### Changed

- Updated client setup checklist with demo setup

---

## [1.2.0] - 2026-01-20

### Added

- Prompt management documentation
- Version history feature docs

### Changed

- Updated API reference for prompts

---

## [1.1.0] - 2026-01-15

### Added

- Initial deployment guide
- Client setup checklist
- Basic troubleshooting

---

## [1.0.0] - 2026-01-10

### Added

- Initial documentation structure
- README.md
- Basic getting started guide

---

## Versioning Policy

- Documentation version matches application version
- Major versions: Significant restructuring
- Minor versions: New guides or major updates
- Patch versions: Corrections and clarifications

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for documentation contribution guidelines.
