# Helix Architecture

## Overview

Helix is our standardized RAG chatbot framework. Each client deployment is a configured instance of this codebase.

**Origin**: Productized from PALAI (our PhilRice deployment). The architecture was proven there; Helix makes it repeatable.

## Deployment Model

**One instance per client, fully isolated:**

```
Helix (source repo)
    ├── Fork → Client A instance (own DB, own config)
    ├── Fork → Client B instance (own DB, own config)
    └── Fork → Client C instance (own DB, own config)
```

- No shared database
- No tenant_id columns
- Configuration via environment variables
- Each instance completely isolated

## What Helix Provides

| Component | Description |
|-----------|-------------|
| FastAPI backend | Async API, auto-generated docs |
| React + Vite frontend | Admin dashboard |
| Chat pipeline | 8 processors (language, moderation, RAG, LLM, etc.) |
| QA pair management | CRUD, import, embedding generation |
| Semantic search | pgvector for RAG retrieval |
| LLM integration | OpenAI primary, Anthropic fallback |
| Response caching | Redis-based |
| Conversation memory | Context window management |
| Cost tracking | Per-request, daily aggregates |
| Facebook Messenger | Webhook integration |
| Prompt management | Versioned, editable via admin UI |
| White-label config | Environment-driven branding |

---

## System Overview

Helix is a RAG (Retrieval-Augmented Generation) chatbot platform built as a monolithic FastAPI application with modular pipeline processors.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌─────────────────┐   │
│   │ Facebook │     │Embeddable│     │Standalone│     │    Admin UI     │   │
│   │Messenger │     │  Widget  │     │  Widget  │     │(QA, Analytics)  │   │
│   └────┬─────┘     └────┬─────┘     └────┬─────┘     └───────┬─────────┘   │
│        │                │                │                   │             │
│        └────────────────┴────────────────┴───────────────────┘             │
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
| Embeddable Widget | REST API | `/chat`, `/branding`, `/widget/config` |
| Standalone Widget | REST API | `/widget/standalone`, `/chat` |
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
┌─────────────┐       ┌─────────────┐
│   QAPair    │       │  Embedding  │
├─────────────┤──────<├─────────────┤
│ id          │       │ vector[1536]│
│ question    │       │ qa_pair_id  │
│ answer      │       └─────────────┘
│ category    │
│ status      │
└─────────────┘

┌─────────────────┐       ┌─────────────────┐
│ PromptTemplate  │──────<│ PromptVersion   │
├─────────────────┤       ├─────────────────┤
│ id              │       │ id              │
│ name            │       │ template_id     │
│ description     │       │ content         │
│ type            │       │ version_number  │
└─────────────────┘       │ is_active       │
                          │ created_at      │
                          └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│  Conversation   │──────<│ ObservabilityEvent│
├─────────────────┤       ├─────────────────┤
│ id              │       │ id              │
│ device_id       │       │ conversation_id │
│ platform        │       │ event_type      │
│ created_at      │       │ payload         │
└─────────────────┘       │ timestamp       │
                          └─────────────────┘
```

### Entity Relationships

```
QAPair has one Embedding (vector)
PromptTemplate has many Versions (audit trail)
Conversation has many ObservabilityEvents
CostRecord aggregated by day/month
```

### Single-Tenant Architecture

- **Model**: Each client instance has its own dedicated database
- **Isolation**: Complete separation - no shared infrastructure
- **Configuration**: Instance-specific values via environment variables
- **Deployment**: Fork the repo, configure .env, deploy

---

## External Systems

| System | Purpose | Integration Type | Provider |
|--------|---------|-----------------|----------|
| Facebook Messenger | Chat channel | Webhook | Meta |
| OpenAI | LLM generation + embeddings | REST API | OpenAI |
| Anthropic | LLM fallback | REST API | Anthropic |
| Google Translate | Multi-language support | REST API | Google |

---

## LLM Integration Architecture

### Overview

The LLM integration layer abstracts provider interactions behind a unified interface. The chatbot doesn't care whether it's talking to OpenAI or Anthropic - it just needs responses and embeddings.

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Integration Layer                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Pipeline → LLMService → FallbackOrchestrator → Providers      │
│                  │                │                              │
│                  ▼                ▼                              │
│            ResponseCache     HealthTracker                       │
│                  │                                               │
│                  ▼                                               │
│            CostTracker → CostRecord (DB)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **LLMProvider** | Abstract interface for generate() and embed() |
| **OpenAIProvider** | Primary provider - GPT-4o-mini + embeddings |
| **AnthropicProvider** | Fallback provider - Claude (no embeddings) |
| **FallbackOrchestrator** | Automatic failover between providers |
| **HealthTracker** | Track provider health, trigger cooldowns |
| **ResponseCache** | Redis cache for identical queries |
| **CostTracker** | Record token usage and costs |
| **TokenCounter** | Count tokens, truncate context |

### Fallback Chain

```
1. Check ResponseCache
   └─ HIT → Return cached response (instant, free)
   └─ MISS → Continue

2. Try Primary Provider (OpenAI)
   └─ SUCCESS → Cache response, track cost, return
   └─ TIMEOUT/ERROR → Continue

3. Try Fallback Provider (Anthropic)
   └─ SUCCESS → Cache response, track cost, return
   └─ TIMEOUT/ERROR → Continue

4. Graceful Degradation
   └─ Return apologetic message
   └─ Log all failures for monitoring
```

### Provider Interface

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text completion."""

    @abstractmethod
    async def embed(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings for texts."""

    @property
    @abstractmethod
    def supports_embeddings(self) -> bool:
        """Whether this provider supports embeddings."""
```

### Cost Tracking

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4o | $2.50 | $10.00 |
| claude-3-haiku | $0.25 | $1.25 |
| claude-3.5-sonnet | $3.00 | $15.00 |
| text-embedding-3-small | $0.02 | - |

### Token Management

| Setting | Value |
|---------|-------|
| Max context tokens | 4000 |
| Max output tokens | 1024 |
| Reserved for output | 1024 |
| Truncation strategy | Oldest history first |

---

## API Surface

### Chat API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Send chat message |
| `/health` | GET | Health check |

### Widget API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/widget/config` | GET | Widget configuration (position, placeholder, enabled) |
| `/widget/standalone` | GET | Full-page chat interface (HTML) |
| `/branding` | GET | Branding config (existing, used by widget) |

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
| Admin API | API Key | Header: `X-API-Key` (configured per instance) |
| Chat Users | Device ID | Anonymous, tracked by `device_id` |
| Messenger Webhook | Signature | Facebook signature validation |

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

- Each client has dedicated database (complete isolation)
- Soft delete with retention policies
- Conversation data retention: 30 days default

---

## Chat Widget Architecture

### Overview

The chat widget is a lightweight, embeddable JavaScript bundle that clients add to their websites with a single script tag. It provides the simplest integration path for end users.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Chat Widget System                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client Website                    Helix Backend                 │
│  ┌─────────────┐                  ┌─────────────┐               │
│  │ <script>    │  ──── fetch ──▶  │ /branding   │               │
│  │ widget.js   │                  │ /widget/cfg │               │
│  └─────────────┘                  └─────────────┘               │
│        │                                 │                       │
│        ▼                                 │                       │
│  ┌─────────────┐                         │                       │
│  │ Chat Bubble │  ◀─── config ──────────┘                       │
│  │   Window    │                                                 │
│  │   Messages  │  ──── POST /chat ──▶  ChatOrchestrator         │
│  └─────────────┘                                                 │
│        │                                                         │
│        ▼                                                         │
│  ┌─────────────┐                                                 │
│  │ localStorage│  (message persistence)                         │
│  └─────────────┘                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Widget Components

| Component | Responsibility |
|-----------|----------------|
| **ChatBubble** | Floating button to open/close chat |
| **ChatWindow** | Expandable container with header and body |
| **MessageList** | Scrollable message display |
| **InputArea** | Text input with send button |
| **TypingIndicator** | Loading state while waiting for response |

### Widget Services

| Service | Responsibility |
|---------|----------------|
| **BrandingService** | Fetch and apply branding from `/branding` |
| **ChatClient** | Send messages to `/chat` API |
| **DeviceManager** | Generate and persist device_id |
| **PersistenceService** | Store conversation in localStorage |
| **MessageState** | Manage conversation state and UI updates |

### Deployment Modes

| Mode | Use Case | URL |
|------|----------|-----|
| **Embedded** | Script tag on client website | `<script src="helix-api.../widget.js">` |
| **Standalone** | QR codes, kiosks, direct links | `/widget/standalone` |

### Bundle Requirements

- Size: < 50KB gzipped
- Dependencies: None (self-contained IIFE)
- Scope: Isolated (no global pollution)
- Styles: CSS-in-JS (no host page conflicts)

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

## Testing Architecture

### Test Pyramid

```
        ┌───────────────┐
        │     E2E       │  ← Few, slow, high confidence
        │   (Playwright)│
        ├───────────────┤
        │  Integration  │  ← Primary focus, API-level
        │   (pytest)    │
        ├───────────────┤
        │     Unit      │  ← Fast, isolated, many
        │   (pytest)    │
        └───────────────┘
```

| Layer | Scope | Tools | Count Target |
|-------|-------|-------|--------------|
| Unit | Single function/class | pytest, mock | Many (100+) |
| Integration | API endpoints, DB | pytest, httpx, testcontainers | Moderate (50+) |
| E2E | Full user flows | Playwright | Few (10-20) |

### Directory Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures (db, client, factories)
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_chat_flow.py
│   │   ├── test_tenant_isolation.py
│   │   ├── test_prompt_management.py
│   │   └── test_qa_management.py
│   └── unit/
│       ├── __init__.py
│       ├── test_pipeline_processors.py
│       ├── test_services.py
│       └── test_repositories.py
│
frontend/
├── tests/
│   ├── components/
│   │   ├── Dashboard.test.tsx
│   │   ├── PromptEditor.test.tsx
│   │   └── ChatWidget.test.tsx
│   └── e2e/
│       ├── chat-flow.spec.ts
│       └── admin-flow.spec.ts
```

### Fixtures and Factories

```python
# backend/tests/conftest.py

@pytest.fixture
def db_session():
    """Isolated database session per test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()

@pytest.fixture
def test_qa_pair(db_session):
    """Create test QA pair"""
    qa_pair = QAPairFactory.create(question="Test Q", answer="Test A")
    db_session.add(qa_pair)
    db_session.commit()
    return qa_pair

@pytest.fixture
def client(db_session):
    """Test client with database session"""
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)
```

### Database Setup/Teardown

| Strategy | When to Use |
|----------|-------------|
| In-memory SQLite | Unit tests, fast integration tests |
| Testcontainers PostgreSQL | Full integration with pgvector |
| Transaction rollback | Isolation between tests |

```python
# Transaction rollback pattern
@pytest.fixture(autouse=True)
def rollback(db_session):
    yield
    db_session.rollback()
```

### Testing Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Test runner, fixtures |
| **pytest-cov** | Coverage reporting (target: 80%) |
| **httpx** | Async test client |
| **factory_boy** | Test data factories |
| **Vitest** | Frontend unit tests |
| **Testing Library** | React component testing |
| **MSW** | API mocking for frontend |
| **Playwright** | E2E browser tests |

### Running Tests

```bash
# All tests
python helix.py test

# Backend only
python helix.py test backend

# Frontend only
python helix.py test frontend

# Specific test types
python helix.py test unit
python helix.py test integration

# With coverage
cd backend && pytest --cov=. --cov-report=html
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Development Guidelines](00_development_guidelines.md) | TDD workflow and standards |
| [Overview](01_overview.md) | What Helix is and why we built it |
| [Deployment Guide](../docs/deployment-guide.md) | How to deploy for a client |

---

*Last updated: January 2026*
