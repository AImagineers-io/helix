# Helix

**White-label RAG Chatbot Platform**

Helix helps government agencies and research institutions deploy AI-powered Q&A chatbots so they can serve citizens 24/7 in their own language, without expensive call centers or hallucinating answers.

---

## What is Helix?

Helix is a retrieval-augmented generation (RAG) chatbot platform that answers questions from your curated knowledge base. Unlike general-purpose AI assistants, Helix grounds all responses in YOUR approved content, eliminating hallucinations and ensuring accurate, compliant answers.

### Key Features

- **RAG-Powered Q&A** - Answers questions strictly from your knowledge base
- **Multi-language Support** - Detects user language, processes in English, responds in original language
- **Multi-channel** - Web widget, Facebook Messenger, REST API
- **Admin Dashboard** - QA management, prompt editing, analytics, conversation review
- **Cost Tracking** - Built-in budget alerts and usage monitoring
- **White-label** - Fully customizable branding per client

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/aimagineers/helix.git
cd helix
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/helix_db
OPENAI_API_KEY=sk-your-openai-key
APP_NAME=Your Company AI
BOT_NAME=YourBot
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

### 4. Seed Initial Data

```bash
python helix.py seed prompts
```

### 5. Access Application

- Frontend: http://localhost:8015
- Backend API: http://localhost:8014
- API Docs: http://localhost:8014/docs

---

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   Backend    │─────▶│  PostgreSQL │
│ React/Vite  │      │   FastAPI    │      │  + pgvector │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                     ┌──────▼───────┐
                     │    Redis     │
                     │ Cache/Memory │
                     └──────────────┘
```

**Tech Stack:**

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React + Vite + TypeScript | Modern UI with type safety |
| Backend | FastAPI (Python 3.11+) | Async API, auto-generated docs |
| Database | PostgreSQL + pgvector | Vector search for RAG |
| Cache | Redis | Response caching, conversation memory |
| Deployment | Docker Compose | Simple deployment, Kubernetes-ready |

---

## Configuration

### Branding (White-label)

Customize your instance via environment variables:

```bash
# Application branding
APP_NAME=Your Company AI Assistant
APP_DESCRIPTION=AI-powered Q&A for your organization
BOT_NAME=YourBot
LOGO_URL=https://your-domain.com/logo.png
PRIMARY_COLOR=#3B82F6

# Feature flags
ENABLE_MESSENGER=true
ENABLE_ANALYTICS=true
```

### LLM Providers

```bash
# Primary provider
OPENAI_API_KEY=sk-your-key

# Fallback provider (optional)
ANTHROPIC_API_KEY=sk-ant-your-key
```

### Database

```bash
# PostgreSQL (production)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# SQLite (development/demo)
DATABASE_URL=sqlite:///./helix.db
```

---

## Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Manual Deployment

```bash
# Backend
cd 02_backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd 03_frontend
npm install
npm run build
npm run preview
```

### Production Deployment

See [Deployment Guide](docs/deployment-guide.md) for complete production setup including:
- PostgreSQL configuration
- Cloudflare tunnel setup
- Facebook Messenger integration
- Monitoring and backups

---

## Usage

### Seeding Data

```bash
# Seed default prompts
python helix.py seed prompts

# Seed demo data
python helix.py seed demo

# Reset database and reseed
python helix.py seed reset
```

### Running Tests

```bash
# All tests
python helix.py test

# Backend only
python helix.py test backend

# Frontend only
python helix.py test frontend

# Unit tests only
python helix.py test unit
```

### Health Check

```bash
# Check backend status
python helix.py health

# Or via API
curl http://localhost:8014/health
```

---

## Development

### CLI Tools

Helix includes a CLI for common development tasks:

```bash
# Testing
python helix.py test              # Run all tests
python helix.py test backend      # Backend tests only
python helix.py test unit         # Unit tests only

# Database seeding
python helix.py seed demo         # Seed demo data
python helix.py seed prompts      # Seed default prompts
python helix.py seed reset        # Reset and reseed

# Utilities
python helix.py version           # Show version
python helix.py health            # Check backend health
```

### Project Structure

```
helix/
├── 00_project_roadmap/    # Implementation phases and plans
├── 01_documentation/      # Technical documentation
├── 02_backend/           # FastAPI backend
│   ├── api/             # API routes and schemas
│   ├── core/            # Config and utilities
│   ├── database/        # Models and seeds
│   └── services/        # Business logic
├── 03_frontend/          # React frontend
│   ├── src/pages/       # Page components
│   ├── src/components/  # Reusable components
│   └── src/services/    # API clients
├── 04_tests/            # Test suite
│   ├── integration/     # Integration tests
│   └── unit/           # Unit tests
├── docs/               # User documentation
├── docker-compose.yml  # Docker deployment config
├── helix.py           # CLI tool
└── README.md          # This file
```

### Testing Strategy

Helix uses strict Test-Driven Development (TDD):

1. **Write tests first** (RED) - Define expected behavior
2. **Implement minimum code** (GREEN) - Make tests pass
3. **Refactor** - Improve code quality while keeping tests green

See [Development Guidelines](00_project_roadmap/00_development_guidelines.md) for TDD workflow.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Deployment Guide](docs/deployment-guide.md) | Complete production deployment guide |
| [Client Setup Checklist](docs/client-setup-checklist.md) | Step-by-step client onboarding |
| [Architecture Overview](00_project_roadmap/02_architecture.md) | System design and patterns |
| [Development Guidelines](00_project_roadmap/00_development_guidelines.md) | TDD workflow and standards |
| [Technical Product Brief](01_documentation/helix-technical-product-brief.md) | Complete technical specs |

---

## API Endpoints

### Chat API

```bash
POST /chat
# Send chat message, get AI response

GET /health
# Health check endpoint
```

### Admin API

```bash
GET /prompts
# List prompt templates

POST /prompts
# Create new prompt template

PUT /prompts/{id}
# Update prompt (creates new version)

POST /prompts/{id}/publish
# Publish prompt version
```

### Analytics API

```bash
GET /costs/summary
# Cost dashboard data

GET /analytics/conversations
# Conversation analytics
```

See full API documentation at `/docs` endpoint when backend is running.

---

## Roadmap

- [x] **P0** - White-label configuration foundation
- [x] **P1** - Prompt management backend
- [x] **P2** - Prompt admin UI
- [x] **P3** - Admin dashboard improvements
- [x] **P4** - Rebranding and cleanup
- [x] **P5** - Demo and documentation
- [ ] **P6+** - Additional features (see `00_project_roadmap/`)

---

## Support

### Issues and Questions

- **GitHub Issues**: https://github.com/aimagineers/helix/issues
- **Documentation**: [docs/](docs/)
- **Email**: support@aimagineers.io

### Contributing

This is a proprietary product developed by AImagineers. For collaboration inquiries, contact: dev@aimagineers.io

---

## License

**Proprietary** - AImagineers

Copyright © 2026 AImagineers. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

## Version

**v0.5.0** - Demo and Documentation Release

See [version.json](version.json) for detailed version information.

---

*Built with ❤️ by AImagineers*
