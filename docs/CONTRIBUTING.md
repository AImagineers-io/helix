# Contributing to Helix

Thank you for contributing to Helix! This guide covers code contributions, documentation updates, and screenshot maintenance.

---

## Code Contributions

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/helix.git
cd helix

# Backend setup
cd 02_backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../03_frontend
npm install
```

### Development Workflow

We follow Test-Driven Development (TDD):

1. **RED** - Write failing tests first
2. **GREEN** - Write minimum code to pass
3. **REFACTOR** - Improve code quality

See [Development Guidelines](../00_project_roadmap/00_development_guidelines.md) for details.

### Commit Messages

Use conventional commits:

```
feat: Add user authentication endpoint
fix: Correct response format for /chat endpoint
refactor: Extract prompt service methods
docs: Update API documentation
test: Add tests for QA import
```

### Pull Requests

1. Create feature branch from `main`
2. Write tests first (TDD)
3. Implement feature
4. Ensure all tests pass: `python helix.py test`
5. Submit PR with description

---

## Documentation Updates

### Adding Documentation

1. Create/edit files in `/docs` directory
2. Use Markdown format
3. Include code examples where applicable
4. Update table of contents if needed

### Documentation Style

- Use clear, concise language
- Include examples for complex topics
- Add tables for reference data
- Include "Last updated" footer

---

## Screenshot Maintenance

### When to Update Screenshots

- After UI redesign
- When major features are added
- When branding changes
- When existing screenshots become misleading

### Screenshot Requirements

| Attribute | Requirement |
|-----------|-------------|
| Format | PNG |
| Resolution | 1920x1080 (or retina 2x) |
| Browser | Chrome (latest) |
| Theme | Light mode (unless documenting dark mode) |
| Naming | `feature-name-action.png` |

### Naming Convention

```
dashboard-overview.png
qa-pairs-list.png
prompt-editor-preview.png
chat-widget-conversation.png
```

### Automated Screenshot Capture

Use the screenshot capture script:

```bash
# Capture all predefined screenshots
./scripts/capture_screenshots.sh

# Capture specific page
./scripts/capture_screenshots.sh --page dashboard
```

### Manual Screenshot Process

1. **Prepare environment**
   ```bash
   # Start services with demo data
   docker-compose -f docker-compose.demo.yml up -d
   ```

2. **Set consistent state**
   - Use demo/seed data
   - Clear notifications
   - Set viewport to 1920x1080

3. **Capture screenshot**
   - Use browser DevTools (Cmd+Shift+P → "Capture screenshot")
   - Or use Playwright script

4. **Optimize image**
   ```bash
   # Compress without quality loss
   pngquant --force --output docs/images/screenshot.png docs/images/screenshot.png
   ```

5. **Update documentation**
   - Reference new screenshot in docs
   - Remove old screenshot file
   - Update alt text if needed

### Screenshot Storage

```
docs/
├── images/
│   ├── dashboard/
│   │   ├── overview.png
│   │   └── analytics.png
│   ├── qa-management/
│   │   ├── list-view.png
│   │   └── import-dialog.png
│   └── prompts/
│       ├── editor.png
│       └── version-history.png
```

---

## Testing Contributions

### Running Tests

```bash
# All tests
python helix.py test

# Backend only
python helix.py test backend

# Frontend only
python helix.py test frontend

# With coverage
python helix.py test --coverage
```

### Writing Tests

- Follow AAA pattern (Arrange-Act-Assert)
- Test behavior, not implementation
- Include edge cases
- Mock external services

See [Testing Standards](../00_project_roadmap/00_development_guidelines.md#testing-standards).

---

## Code Quality

### Python

- Format with Black: `black 02_backend/`
- Lint with Ruff: `ruff check 02_backend/`
- Type hints required for public APIs

### TypeScript

- Format with Prettier: `npm run format`
- Lint with ESLint: `npm run lint`
- Strict TypeScript, no `any`

---

## Questions?

- Check existing documentation
- Search GitHub issues
- Open a discussion

---

*Last updated: January 2026*
