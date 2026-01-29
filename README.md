# Helix

**AImagineers Chatbot Deployment Framework**

Helix is our internal platform for deploying production-ready RAG chatbots for clients. It standardizes how we build, configure, and ship knowledge-base chatbots — reducing deployment time from weeks to days.

---

## What is Helix?

Helix is a retrieval-augmented generation (RAG) chatbot framework that we use to deploy chatbots for clients across any industry. Each deployment is white-labeled, isolated, and configured entirely through environment variables — no code changes needed per client.

**Origin**: Productized from PALAI (PhilRice deployment). That project proved the architecture; Helix makes it repeatable.

### Core Capabilities

- **RAG Pipeline** - Answers grounded in client's knowledge base, no hallucinations
- **Multi-language** - Auto-detects language, responds in user's language
- **Multi-channel** - Web widget, Facebook Messenger, REST API
- **Admin Dashboard** - QA management, prompt editing, analytics
- **Cost Tracking** - Built-in usage monitoring and budget alerts
- **White-label Ready** - Branding configured via environment variables

---

## Quick Start (Local Development)

### 1. Clone Repository

```bash
git clone https://github.com/aimagineers/helix.git
cd helix
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with client-specific values
```

Required environment variables:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/helix_db
OPENAI_API_KEY=sk-your-openai-key
APP_NAME=ClientName Assistant    # Client's branded name
BOT_NAME=ClientBot               # Chatbot persona name
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

### Client Branding

Each deployment is configured via environment variables. No code changes needed:

```bash
# Client branding (change per deployment)
APP_NAME=Acme Support Bot
APP_DESCRIPTION=AI assistant for Acme Corp
BOT_NAME=Ada
LOGO_URL=https://acme.com/logo.png
PRIMARY_COLOR=#1E40AF

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
| [Deployment Guide](docs/deployment-guide.md) | How to deploy for a new client |
| [Client Setup Checklist](docs/client-setup-checklist.md) | Step-by-step deployment checklist |
| [Architecture Overview](00_project_roadmap/02_architecture.md) | System design and patterns |
| [Development Guidelines](00_project_roadmap/00_development_guidelines.md) | TDD workflow and standards |
| [Technical Brief](01_documentation/helix-technical-product-brief.md) | Technical specifications |

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

## Team Resources

- **Issues**: https://github.com/aimagineers/helix/issues
- **Documentation**: [docs/](docs/)
- **Questions**: dev@aimagineers.io

---

## License

**Proprietary** - AImagineers

Copyright © 2026 AImagineers. All rights reserved.

---

## Version

**v0.5.0** - Demo and Documentation Release

See [version.json](version.json) for detailed version information.
