# Helix Overview

## Product Summary

**Helix** is a white-label RAG (Retrieval-Augmented Generation) chatbot platform designed for government agencies, research institutions, and enterprises with large knowledge bases.

> Helix helps government agencies and research institutions deploy AI-powered Q&A chatbots so they can serve citizens 24/7 in their own language, without expensive call centers or hallucinating answers.

---

## Problem Statement

### Who Has This Problem?

Organizations with large knowledge bases who need to provide accurate, multilingual, AI-powered Q&A at scale without breaking the budget:

- Government citizen service centers (SSS, PhilHealth, Pag-IBIG)
- Agricultural extension services (PhilRice)
- Regional research institutes (Vietnam CLRRI, Thai Rice Department)
- Enterprise support centers

### The Pain

- Staff overwhelmed with repetitive inquiries
- Inconsistent answers across channels
- Citizens/customers churning or giving up
- Expensive call center costs that scale linearly with demand

---

## Solution

### What Helix Does

| Feature | Description |
|---------|-------------|
| **RAG Chatbot** | Answers questions from your curated knowledge base |
| **Multi-language** | Detects language, processes in English, responds in user's language |
| **Multi-channel** | Web widget, Facebook Messenger, REST API |
| **Admin Dashboard** | QA management, prompt editing, analytics, issue triage |
| **Cost Tracking** | Built-in budget alerts and usage monitoring |
| **White-label** | Customizable branding per client |

### What Helix Does NOT Do

- **Not a general-purpose LLM** - Answers are grounded in YOUR data only (no hallucination)
- **Not a live chat replacement** - Human handoff supported but humans manage separately
- **Not a content authoring tool** - You bring the QA pairs, Helix serves them
- **Not multi-tenant SaaS** - Each client gets their own dedicated deployment

---

## Deployment Model

**Single-tenant, white-label deployments:**

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

Each deployment is isolated, customized, and managed independently.

---

## Deliverables

### Core Deliverables

| Deliverable | Status |
|-------------|--------|
| Dedicated Helix instance (Docker deployment) | Core |
| Chat widget (embeddable web + standalone) | Core |
| Facebook Messenger integration | Core |
| Admin dashboard (QA management, prompts, analytics) | Core |
| REST API for custom integrations | Core |
| QA import tools (CSV, JSON, text) | Core |
| Observability & cost monitoring dashboard | Core |
| White-label branding (logo, colors, bot name) | Core |

### Future / Add-on

| Deliverable | Status |
|-------------|--------|
| WhatsApp integration | Add-on |
| LINE integration | Add-on |
| Viber integration | Add-on |
| Custom LLM fine-tuning | Not planned |
| On-premise deployment | Enterprise only |

---

## Success Metrics

### Timeline Milestones

| Milestone | Target |
|-----------|--------|
| **30 days** | Chatbot live with 500+ QA pairs, handling first real user queries |
| **60 days** | 70%+ of inquiries resolved without human intervention |
| **90 days** | Measurable reduction in repetitive support tickets, cost per query < $0.01 |

### Performance Targets

| Metric | Target |
|--------|--------|
| Inquiry deflection rate | 70%+ |
| Response time | < 2 seconds |
| Monthly LLM cost (10k queries) | < $30 |
| Cache hit rate | 30%+ |

---

## Prerequisites

### What Clients Need to Provide

1. **QA Pairs** - Structured format (CSV/Excel), minimum 200 pairs recommended
2. **Facebook Page Access** - If Messenger deployment needed
3. **Brand Assets** - Logo, colors, bot name for white-labeling
4. **Subject Matter Expert** - 2-4 hours/week during onboarding for QA review

### Technical Requirements

- Approved knowledge base content
- Decision maker available for weekly check-ins
- Budget for LLM API costs (~$10-30/month depending on volume)

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

## Project Origin

Helix is productized from **PALAI**, a successful deployment for PhilRice (Philippine Rice Research Institute). The conversion involves:

- Removing client-specific branding and data
- Abstracting client-specific values to configuration
- Adding multi-tenant support
- Creating provisioning and deployment documentation
- Building demo capabilities

---

## Current Status

| Area | Status |
|------|--------|
| Problem Clarity | Complete |
| Solution Boundaries | Complete |
| Deliverable Clarity | In Progress (need demo assets) |
| Outcome Definition | Complete |
| Commercials | Complete |
| Prerequisites | Complete |
| Technical Abstraction | In Progress |
| Documentation | In Progress |

**Overall: In Development**

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Development Guidelines](00_development_guidelines.md) | TDD workflow, testing standards, code quality |
| [Architecture](02_architecture.md) | System design, data model, API surface |
| [Productization Framework](../01_documentation/helix-productization-framework.md) | Full product readiness checklist |
| [Technical Product Brief](../01_documentation/helix-technical-product-brief.md) | Detailed technical specifications |

---

*Last updated: January 2025*
*Helix v0.1.0*
