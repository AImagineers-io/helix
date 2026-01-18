# Helix Architecture

## System Overview

Helix is a RAG (Retrieval-Augmented Generation) chatbot platform built as a monolithic FastAPI application with modular pipeline processors.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌──────────┐     ┌──────────┐     ┌──────────────────────────────────┐   │
│   │ Facebook │     │   Web    │     │          Admin UI                │   │
│   │Messenger │     │  Widget  │     │  (QA Mgmt, Analytics, Prompts)   │   │
│   └────┬─────┘     └────┬─────┘     └───────────────┬──────────────────┘   │
│        │                │                           │                       │
│        └────────────────┴───────────────────────────┘                       │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                │
│                    │     FastAPI Server    │                                │
│                    │  ┌─────────────────┐  │                                │
│                    │  │ Chat Orchestrator│  │                                │
│                    │  │    Pipeline      │  │                                │
│                    │  └────────┬────────┘  │                                │
│                    └───────────┼───────────┘                                │
│                                │                                            │
│        ┌───────────┬───────────┼───────────┬───────────┐                    │
│        ▼           ▼           ▼           ▼           ▼                    │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│   │ Prompt  │ │  Redis  │ │PostgreSQL│ │   LLM   │ │Translate│              │
│   │ Service │ │ (Cache/ │ │(QA Pairs/│ │ Provider│ │ Service │              │
│   │  (DB)   │ │ Memory) │ │ Vectors) │ │ (OpenAI/│ │(Google) │              │
│   └─────────┘ └─────────┘ └─────────┘ │Anthropic)│ └─────────┘              │
│                                       └─────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Topology

### AImagineers Homelab Infrastructure

Helix is deployed on the AImagineers homelab infrastructure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                          │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────┐                                      │
│                    │   Cloudflare    │                                      │
│                    │     Tunnel      │                                      │
│                    │  (aimph-tunnel) │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│    ┌────────────────────────┼────────────────────────┐                      │
│    │                        │                        │                      │
│    ▼                        ▼                        ▼                      │
│ helix.aimagineers.io   helix-api.aimagineers.io   (other services)         │
│    │                        │                                               │
│    └────────────────────────┼───────────────────────────────────────────────┘
│                             │
├─────────────────────────────┼───────────────────────────────────────────────┤
│                      HOMELAB NETWORK                                        │
│                             │                                               │
│  ┌──────────────────────────┴──────────────────────────┐                    │
│  │                     apps01                           │                    │
│  │               192.168.20.xxx                         │                    │
│  │                 4 vCPU / 8GB RAM                     │                    │
│  ├──────────────────────────────────────────────────────┤                    │
│  │                                                      │                    │
│  │  ┌─────────────────┐  ┌─────────────────┐           │                    │
│  │  │ helix-frontend  │  │  helix-backend  │           │                    │
│  │  │    :8015        │  │     :8014       │           │                    │
│  │  │   (React/Vite)  │  │    (FastAPI)    │           │                    │
│  │  └─────────────────┘  └─────────────────┘           │                    │
│  │                                                      │                    │
│  │  ┌─────────────────┐                                │                    │
│  │  │  helix-redis    │                                │                    │
│  │  │    :6381        │                                │                    │
│  │  └─────────────────┘                                │                    │
│  │                                                      │                    │
│  └──────────────────────────────────────────────────────┘                    │
│                             │                                               │
│                             │ PostgreSQL Connection                         │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────┐                    │
│  │                      db01                            │                    │
│  │               192.168.30.xxx                         │                    │
│  │                 4 vCPU / 8GB RAM                     │                    │
│  ├──────────────────────────────────────────────────────┤                    │
│  │                                                      │                    │
│  │  ┌─────────────────────────────────────────┐        │                    │
│  │  │           PostgreSQL + pgvector          │        │                    │
│  │  │               :5432                      │        │                    │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │        │                    │
│  │  │  │ helix_db│ │palai_db │ │pulse_db │   │        │                    │
│  │  │  └─────────┘ └─────────┘ └─────────┘   │        │                    │
│  │  └─────────────────────────────────────────┘        │                    │
│  │                                                      │                    │
│  └──────────────────────────────────────────────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Public URLs

| Service | URL | Internal Port |
|---------|-----|---------------|
| Frontend | `https://helix.aimagineers.io` | 8015 |
| Backend API | `https://helix-api.aimagineers.io` | 8014 |

### Port Allocation

| Service | External Port | Internal Port | Notes |
|---------|---------------|---------------|-------|
| helix-backend | 8014 | 8000 | FastAPI server |
| helix-frontend | 8015 | 3000 | Vite preview server |
| helix-redis | 6381 | 6379 | Cache/memory store |

**Existing services on apps01:**
- PALAI: 8007 (backend), 8008 (frontend), 6380 (redis)
- Pulse: 8011 (backend), 8012 (frontend)
- Stage: 8009 (backend), 8010 (frontend)

### VM Resources

| VM | IP Range | vCPU | RAM | Purpose |
|----|----------|------|-----|---------|
| apps01 | 192.168.20.xxx | 4 | 8GB | Docker containers |
| db01 | 192.168.30.xxx | 4 | 8GB | PostgreSQL server |
| gitlab01 | 192.168.40.xxx | 4 | 6GB | GitLab |
| gitrunner01 | 192.168.20.xxx | 2 | 3GB | CI/CD runner |
| ops01 | 192.168.40.xxx | 2 | 4GB | Monitoring |

### Cloudflare Tunnel Configuration

The tunnel exposes services without opening firewall ports:

```yaml
# Add to cloudflared config on apps01
ingress:
  # Helix Frontend
  - hostname: helix.aimagineers.io
    service: http://localhost:8015

  # Helix Backend API
  - hostname: helix-api.aimagineers.io
    service: http://localhost:8014
```

**DNS Records (Cloudflare):**
- `helix` CNAME → `<tunnel-id>.cfargotunnel.com`
- `helix-api` CNAME → `<tunnel-id>.cfargotunnel.com`

### Future: Kubernetes-Ready

The architecture is designed to scale to Kubernetes when needed, with each component as a separate deployment.

---

## Data Flow

### Inbound

| Source | Method | Endpoint |
|--------|--------|----------|
| Facebook Messenger | Webhook | `/messenger/webhook` |
| Web Widget | REST API | `/chat` |
| Admin UI | REST API | Various `/api/*` endpoints |
| QA Import | REST API | `/qa/import/*` |

### Outbound

| Destination | Method | Purpose |
|-------------|--------|---------|
| Messenger API | REST | Send responses to users |
| OpenAI/Anthropic | REST | LLM generation + embeddings |
| Google Translate | REST | Multi-language support |
| SSE Streams | Server-Sent Events | Real-time observability |

---

## Core Components

### Chat Orchestrator Pipeline

The heart of Helix - processes incoming messages through a series of processors:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Chat Orchestrator Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Message In → [Language] → [Translate] → [Moderation] →         │
│              Detection      to English                           │
│                                                                  │
│            → [Intent] → [Handler] → [RAG] → [LLM] →             │
│              Classification Selection  Retrieval Generation      │
│                                                                  │
│            → [Translate] → [Response] → Message Out             │
│              to User Lang   Formatting                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Pipeline Processors

| Processor | Responsibility |
|-----------|----------------|
| **LanguageDetectionProcessor** | Detect user's language |
| **TranslationProcessor** | Translate to/from English |
| **ModerationProcessor** | Content filtering (profanity, off-topic) |
| **IntentClassificationProcessor** | Classify intent (greeting, farewell, question) |
| **HandlerSelectionProcessor** | Route to appropriate handler |
| **RAGRetrievalProcessor** | Find relevant QA pairs via similarity search |
| **LLMGenerationProcessor** | Generate response using LLM |
| **ResponseFormattingProcessor** | Format final response |

### Prompt Service

Manages configurable LLM prompts with versioning:

```
┌─────────────────────────────────────────────────────────┐
│                    Prompt Service                        │
├─────────────────────────────────────────────────────────┤
│  • CRUD operations for prompt templates                 │
│  • Version history with rollback capability             │
│  • Per-tenant overrides with global defaults            │
│  • A/B testing support (traffic % split)               │
│  • Draft → Preview → Publish workflow                   │
└─────────────────────────────────────────────────────────┘
```

### QA Service

Manages the knowledge base:

```
┌─────────────────────────────────────────────────────────┐
│                      QA Service                          │
├─────────────────────────────────────────────────────────┤
│  • CRUD operations for QA pairs                         │
│  • Bulk import (CSV, JSON, text)                        │
│  • Automatic embedding generation (background job)      │
│  • Status workflow: draft → pending_review → active     │
│  • Category/tag management                              │
└─────────────────────────────────────────────────────────┘
```

---

## Data Model

### Core Entities

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Tenant    │──────<│   QAPair    │       │  Embedding  │
├─────────────┤       ├─────────────┤──────<├─────────────┤
│ id          │       │ id          │       │ vector[1536]│
│ name        │       │ tenant_id   │       │ qa_pair_id  │
│ config      │       │ question    │       └─────────────┘
│ branding    │       │ answer      │
└─────────────┘       │ category    │
      │               │ status      │
      │               └─────────────┘
      │
      │         ┌─────────────────┐       ┌─────────────────┐
      └────────<│ PromptTemplate  │──────<│ PromptVersion   │
                ├─────────────────┤       ├─────────────────┤
                │ id              │       │ id              │
                │ tenant_id       │       │ template_id     │
                │ name            │       │ content         │
                │ description     │       │ version_number  │
                └─────────────────┘       │ is_active       │
                                          │ created_at      │
      │                                   └─────────────────┘
      │
      │         ┌─────────────────┐       ┌─────────────────┐
      └────────<│  Conversation   │──────<│ ObservabilityEvent│
                ├─────────────────┤       ├─────────────────┤
                │ id              │       │ id              │
                │ tenant_id       │       │ conversation_id │
                │ device_id       │       │ event_type      │
                │ platform        │       │ payload         │
                │ created_at      │       │ timestamp       │
                └─────────────────┘       └─────────────────┘
```

### Entity Relationships

```
Tenant has many QAPairs
Tenant has many PromptTemplates
Tenant has many Conversations
Conversation has many ObservabilityEvents
QAPair has one Embedding (vector)
PromptTemplate has many Versions (audit trail)
CostRecord belongs to Tenant (aggregated by day/month)
```

### Multi-Tenancy

- **Model**: Shared database with `tenant_id` on all tables
- **Enforcement**: Repository layer filters all queries by `tenant_id`
- **Isolation**: No cross-tenant data access possible at the data layer

---

## External Systems

| System | Purpose | Integration Type | Provider |
|--------|---------|-----------------|----------|
| Facebook Messenger | Chat channel | Webhook | Meta |
| OpenAI | LLM generation + embeddings | REST API | OpenAI |
| Anthropic | LLM fallback | REST API | Anthropic |
| Google Translate | Multi-language support | REST API | Google |

---

## API Surface

### Chat API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Send chat message |
| `/health` | GET | Health check |

### QA Management API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/qa/pairs` | GET | List QA pairs (paginated) |
| `/qa/pairs` | POST | Create QA pair |
| `/qa/pairs/{id}` | GET | Get single QA pair |
| `/qa/pairs/{id}` | PUT | Update QA pair |
| `/qa/pairs/{id}` | DELETE | Delete QA pair (soft) |
| `/qa/import/text` | POST | Bulk import from text |
| `/qa/import/csv` | POST | Bulk import from CSV |

### Prompt Management API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/prompts` | GET | List prompt templates |
| `/prompts` | POST | Create prompt template |
| `/prompts/{id}` | GET | Get prompt with versions |
| `/prompts/{id}` | PUT | Update prompt (creates version) |
| `/prompts/{id}/publish` | POST | Publish version |
| `/prompts/{id}/rollback` | POST | Rollback to previous version |

### Analytics API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/costs/summary` | GET | Cost dashboard data |
| `/analytics/conversations` | GET | Conversation analytics |
| `/observability/events/stream` | GET | SSE event stream |

### Webhook API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/messenger/webhook` | GET | Facebook verification |
| `/messenger/webhook` | POST | Incoming Messenger messages |

---

## Authentication

| Context | Method | Details |
|---------|--------|---------|
| Admin API | API Key | Header: `X-API-Key` |
| Chat Users | Device ID | Anonymous, tracked by `device_id` |
| Messenger Webhook | Signature | Facebook signature validation |
| Tenant Identification | Header | `X-Tenant-ID` for multi-tenant |

---

## Caching Strategy

### Redis Usage

| Purpose | TTL | Key Pattern |
|---------|-----|-------------|
| Response cache | 24 hours | `response:{tenant}:{hash}` |
| Conversation memory | 30 minutes | `memory:{conversation_id}` |
| Rate limiting | 1 minute | `ratelimit:{device_id}` |
| Session data | 24 hours | `session:{device_id}` |

### Cache Hit Targets

- Response cache hit rate: 30%+
- Conversation memory: 100% for active sessions

---

## Error Handling & Graceful Degradation

### LLM Provider Down

```
1. Try primary provider (OpenAI)
2. If timeout/error → Try fallback provider (Anthropic)
3. If both fail → Check response cache for similar queries
4. If no cache → Return apologetic fallback message
```

### Rate Limiting

- 60 requests/minute per device
- 429 response with `Retry-After` header
- Graceful degradation: cached responses still served

### Unexpected Errors

- Log full error with context for review
- Return safe, generic error message to user
- Flag conversation for human review

---

## Observability

### Metrics Collected

| Metric | Purpose |
|--------|---------|
| Request latency | Performance monitoring |
| Token usage | Cost tracking |
| Cache hit rate | Efficiency monitoring |
| Error rate | Reliability tracking |
| Deflection rate | Business KPI |

### Event Types

| Event | Trigger |
|-------|---------|
| `message_received` | User sends message |
| `intent_classified` | Intent determined |
| `retrieval_complete` | RAG query finished |
| `response_generated` | LLM response ready |
| `response_sent` | Message delivered |
| `error_occurred` | Any error |

---

## Security Considerations

### Input Validation

- Content filtering (profanity, off-topic detection)
- Length limits (10,000 chars max)
- Rate limiting (60 req/min per device)
- SQL injection prevention (parameterized queries)

### Output Validation

- Hallucination checks (responses grounded in context only)
- Format validation (structured response templates)
- PII filtering (planned)

### Data Protection

- Tenant isolation at repository layer
- Soft delete with retention policies
- Conversation data retention: 30 days default

---

## Messenger Webhook Architecture

### V1 vs V2 Webhooks

```
┌─────────────────────────────────────────────────────────────────┐
│                    Messenger Integration                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Facebook → /messenger/webhook (V1) → Legacy Handler → User    │
│              [PRODUCTION - DO NOT MODIFY]                        │
│                                                                  │
│   Facebook → /messenger/v2/webhook (V2) → ChatOrchestrator →    │
│              [DEVELOPMENT - New features here]                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Safety Rules

1. **V1 is PRODUCTION** - Never modify without approval
2. **V2 for development** - All new features go here
3. **Gradual migration** - When V2 is stable, reconfigure Facebook
4. **Testing required** - Integration tests for all webhook changes

---

## Background Jobs

### Job Types

| Job | Trigger | Purpose |
|-----|---------|---------|
| Embedding generation | QA pair created/updated | Generate vector embeddings |
| Daily aggregation | Scheduled (midnight) | Aggregate analytics data |
| Cost reporting | Scheduled (daily) | Calculate and alert on costs |
| Conversation archival | Scheduled (weekly) | Archive old conversations |

### Implementation

- FastAPI BackgroundTasks for simple jobs
- Redis queue for longer-running tasks (future)

---

## Scaling Considerations

### Current Limits (Single Server)

| Resource | Limit |
|----------|-------|
| Concurrent connections | ~1000 |
| Requests/second | ~100 |
| Database connections | 20 pool |
| Redis connections | 10 pool |

### Future Scaling Path

1. **Horizontal scaling**: Multiple FastAPI instances behind load balancer
2. **Database**: Read replicas for analytics queries
3. **Cache**: Redis cluster for high availability
4. **Queue**: Dedicated job queue (Celery/RQ) for background tasks
5. **Kubernetes**: Full container orchestration

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Development Guidelines](00_development_guidelines.md) | TDD workflow, testing standards |
| [Overview](01_overview.md) | Product summary, features, success metrics |
| [Technical Product Brief](../01_documentation/helix-technical-product-brief.md) | Full technical specifications |

---

*Last updated: January 2025*
*Helix v0.1.0*
