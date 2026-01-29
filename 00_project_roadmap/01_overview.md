# Helix Overview

## What is Helix?

**Helix** is AImagineers' internal framework for deploying RAG (Retrieval-Augmented Generation) chatbots for clients. It standardizes our deployment process so we can ship production-ready chatbots in days, not weeks.

> Helix lets us deploy white-label chatbots for any client with a knowledge base — configured via environment variables, no code changes per deployment.

---

## Why We Built This

### The Problem We Solve for Clients

Organizations with knowledge bases need accurate, scalable Q&A. Their pain points:

- Staff overwhelmed with repetitive inquiries
- Inconsistent answers across channels
- Expensive support costs that scale linearly with demand

### The Problem We Solve for Ourselves

Before Helix, each chatbot deployment was bespoke. Now:

- **Repeatable**: Same codebase, different config
- **Fast**: Days to deploy, not weeks
- **Maintainable**: One codebase to update, all deployments benefit

---

## Core Capabilities

### What We Deliver to Clients

| Feature | Description |
|---------|-------------|
| **RAG Chatbot** | Answers grounded in client's knowledge base |
| **Multi-language** | Auto-detects language, responds in user's language |
| **Multi-channel** | Web widget, Facebook Messenger, REST API |
| **Admin Dashboard** | QA management, prompt editing, analytics |
| **Cost Tracking** | Usage monitoring and budget alerts |
| **White-label** | Client branding via config, no code changes |

### Scope Boundaries

- **Not a general-purpose LLM** - Answers grounded in knowledge base only
- **Not a live chat replacement** - Human handoff supported, but separate tooling
- **Not a content authoring tool** - Client provides QA pairs, we serve them
- **Not multi-tenant** - Each client gets isolated deployment

---

## Deployment Model

**One instance per client, completely isolated:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client A      │    │   Client B      │    │   Client C      │
│   Instance      │    │   Instance      │    │   Instance      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Own database  │    │ • Own database  │    │ • Own database  │
│ • Own branding  │    │ • Own branding  │    │ • Own branding  │
│ • Own prompts   │    │ • Own prompts   │    │ • Own prompts   │
│ • Own analytics │    │ • Own analytics │    │ • Own analytics │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

Fork the repo, configure `.env`, deploy. Each instance is independent.

---

## What We Ship Per Client

### Standard Deliverables

| Deliverable | Description |
|-------------|-------------|
| Helix instance | Docker deployment on our infra or client's |
| Chat widget | Embeddable web widget + standalone page |
| Messenger integration | Facebook Messenger webhook (if needed) |
| Admin dashboard | QA management, prompts, analytics |
| REST API | For custom integrations |
| QA import tools | CSV, JSON, text import |
| Cost monitoring | Usage tracking and alerts |

### Optional Add-ons

| Add-on | Notes |
|--------|-------|
| WhatsApp integration | Additional setup |
| LINE/Viber integration | Additional setup |
| On-premise deployment | Enterprise engagements only |

---

## Success Metrics (Client-Facing)

What we promise clients:

| Milestone | Target |
|-----------|--------|
| **30 days** | Chatbot live with 500+ QA pairs |
| **60 days** | 70%+ inquiry deflection |
| **90 days** | Cost per query < $0.01 |

### Performance Targets

| Metric | Target |
|--------|--------|
| Inquiry deflection rate | 70%+ |
| Response time | < 2 seconds |
| Monthly LLM cost (10k queries) | < $30 |
| Cache hit rate | 30%+ |

---

## Client Requirements

### What We Need From Clients

1. **QA Pairs** - CSV/Excel format, minimum 200 pairs recommended
2. **Facebook Page Access** - If Messenger integration needed
3. **Brand Assets** - Logo, colors, bot name
4. **SME Availability** - 2-4 hours/week during onboarding for QA review

### Client Budget

- LLM API costs: ~$10-30/month depending on volume
- Hosting: Included in retainer or client provides infrastructure

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Backend** | FastAPI (Python 3.11+) | Async-first, excellent for real-time chat, auto-generated OpenAPI docs |
| **Database** | PostgreSQL + pgvector | Production-grade, vector search built-in for RAG |
| **Cache** | Redis | Conversation memory, response caching, rate limiting |
| **Frontend** | React + Vite + TypeScript | Modern tooling, fast builds, type safety |
| **Mobile** | PWA | No native app needed, web-first |
| **Deployment** | Docker Compose | Simple deploy now, Kubernetes-ready for scale |

---

## AI Components

### Model Selection

| Component | Model | Rationale |
|-----------|-------|-----------|
| **Response Generation** | GPT-4o-mini | Cost-effective, fast, good quality |
| **Fallback Generation** | Claude 3 Haiku | Provider diversity, similar cost profile |
| **Embeddings** | text-embedding-3-small | 1536 dims, good balance of cost/quality |
| **Language Detection** | langdetect library | Fast, no API cost |
| **Translation** | Google Translate API | Reliable, multi-language support |

### RAG Configuration

| Setting | Value |
|---------|-------|
| Vector Store | pgvector (PostgreSQL extension) |
| Chunk Strategy | Document-based (one QA pair = one chunk) |
| Chunk Size | ~200-500 tokens per QA pair |
| Retrieval Method | Cosine similarity |
| Top-K | 3 |

---

## Origin

Helix was productized from **PALAI** (our PhilRice deployment). That engagement proved the architecture works; Helix makes it repeatable for any client.

---

## Current Status

| Area | Status |
|------|--------|
| Core Framework | Complete (P0-P5) |
| Prompt Management | Complete |
| Admin Dashboard | Complete |
| White-label Config | Complete |
| Demo Instance | Complete |
| Documentation | In Progress |

**Overall: Ready for client deployments**

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Development Guidelines](00_development_guidelines.md) | TDD workflow and standards |
| [Architecture](02_architecture.md) | System design and patterns |
| [Deployment Guide](../docs/deployment-guide.md) | How to deploy for a client |
| [Technical Brief](../01_documentation/helix-technical-product-brief.md) | Technical specifications |

---

*Last updated: January 2026*
