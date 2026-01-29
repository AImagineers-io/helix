# Helix Technical Brief

Internal technical specification for the Helix chatbot deployment framework.

---

## Project Header

| Field | Value |
|-------|-------|
| **Product Name** | Helix |
| **Version** | v0.5 |
| **Last Updated** | January 2026 |
| **Author** | AImagineers |
| **Status** | ✅ Ready |

---

# 1. Product Context

**What is this?**
Helix is our internal framework for deploying RAG chatbots for clients. One codebase, configured per client.

**What problem does it solve?**
- **For clients**: Scalable Q&A without expensive support staff
- **For us**: Repeatable deployments, no bespoke development

**Shape of solution:**
Chatbot + Admin Dashboard + API (white-label, single-tenant per client)

**Internal value prop:**

> Deploy production-ready chatbots in days, not weeks. Fork, configure, ship.

---

# 2. Technical Decisions

## Stack Selection

| Layer | Choice | Rationale |
| --- | --- | --- |
| **Backend Framework** | FastAPI | Async-first, excellent for real-time chat, OpenAPI docs auto-generated |
| **Database** | PostgreSQL + pgvector | Production-grade, vector search built-in for RAG |
| **Cache/Queue** | Redis | Conversation memory, response caching, rate limiting |
| **Frontend** | React + Vite + TypeScript | Modern tooling, fast builds, type safety |
| **Mobile** | PWA | No native app needed, web-first |
| **Hosting Target** | Docker Compose → K8s ready | Simple deploy now, scale later |

## Forcing Questions

- [x]  **Why this backend framework?**
    - FastAPI's async support is critical for chat workloads. Auto-generated OpenAPI docs reduce documentation burden. Pydantic validation catches errors early.
- [x]  **Is this a monolith or service-oriented?**
    - [x]  Monolith (default for MVPs)
    - Pipeline processors are modular but deployed as single service
- [x]  **Real-time requirements?**
    - [x]  SSE (what for?): Observability event streaming, typing indicators
    - [x]  Polling acceptable for admin dashboard
- [x]  **Background job requirements?**
    - [x]  Simple (FastAPI BackgroundTasks)
    - *Use cases:* Embedding generation, daily aggregation, cost reporting
- [x]  **File storage requirements?**
    - [x]  Local filesystem (backups)
    - [x]  S3-compatible (future: document uploads)
    - *What types/sizes?* QA import files (CSV/JSON), backup SQL dumps

---

# 3. System Architecture

## High-Level Diagram

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

## External Systems

| System | Purpose | Integration Type | Owner/Provider |
| --- | --- | --- | --- |
| Facebook Messenger | Chat channel | Webhook | Meta |
| OpenAI | LLM generation + embeddings | API | OpenAI |
| Anthropic | LLM fallback | API | Anthropic |
| Google Translate | Multi-language support | API | Google |

## Forcing Questions

- [x]  **What's the deployment topology?**
    - Containerized (Docker Compose), single server initially, K8s-ready
- [x]  **How does data flow in?**
    - *Primary:* Webhook (Messenger), REST API (Web), Admin UI (QA import)
- [x]  **How does data flow out?**
    - *Primary:* Messenger API, REST responses, SSE streams, CSV exports
- [x]  **What breaks if the AI provider is down?**
    - *Graceful degradation:* Cached responses still served, fallback to secondary provider, static "service unavailable" message as last resort

---

# 4. Data Model

## Core Entities

| Entity | Description | Key Relationships |
| --- | --- | --- |
| **Tenant** | Client/organization (multi-tenant) | has many → PromptTemplates, QAPairs, Conversations |
| **QAPair** | Knowledge base question/answer | belongs to → Tenant; has one → Embedding |
| **Conversation** | Chat session with user | belongs to → Tenant; has many → Messages |
| **PromptTemplate** | Configurable LLM prompts | belongs to → Tenant; has many → Versions |
| **ObservabilityEvent** | System event for analytics | belongs to → Conversation |
| **CostRecord** | LLM API cost tracking | belongs to → Tenant |

## Entity Relationship Summary

```
Tenant has many QAPairs
Tenant has many PromptTemplates
Tenant has many Conversations
Conversation has many ObservabilityEvents
QAPair has one Embedding (vector)
PromptTemplate has many Versions (audit trail)
CostRecord belongs to Tenant (aggregated by day/month)
```

## Forcing Questions

- [x]  **Multi-tenancy model?**
    - [x]  Multi-tenant shared DB (tenant_id on tables)
    - Single deployment serves all clients, data isolated by tenant_id
- [x]  **What's the primary entity users interact with?**
    - *Entity:* Conversation (via chat interface)
    - *Lifecycle:* created → active → idle (30min TTL) → archived
- [x]  **What needs to be audited/logged?**
    - Prompt changes (full version history)
    - QA pair changes (status history)
    - All chat interactions (observability events)
    - Cost records (per request)
- [x]  **Soft delete or hard delete?**
    - [x]  Soft delete (deleted_at timestamp)
    - QAPairs, PromptTemplates, Tenants use soft delete
    - ObservabilityEvents hard delete after retention period (30 days)

---

# 5. AI Component Design

## AI Feature Inventory

| Feature | Type | Model/Provider | User-Facing? |
| --- | --- | --- | --- |
| Response Generation | Chat/Completion | GPT-4o-mini / Claude Haiku | Y |
| Semantic Search | Embedding | text-embedding-3-small | N |
| Intent Classification | Classification | Pattern-based + LLM fallback | N |
| Language Detection | Classification | langdetect library | N |
| Translation | Translation | Google Translate API | Y (transparent) |

## LLM Configuration

| Decision | Choice | Rationale |
| --- | --- | --- |
| **Primary Model** | GPT-4o-mini | Cost-effective, fast, good quality |
| **Fallback Model** | Claude 3 Haiku | Provider diversity, similar cost profile |
| **Embedding Model** | text-embedding-3-small | 1536 dims, good balance of cost/quality |
| **Hosting** | API calls | No infra overhead, pay-per-use |

## Prompt Architecture

- [x]  **Prompt management approach:**
    - [x]  Database-stored (editable via Admin UI)
    - Versioned, with A/B testing support
    - Per-tenant overrides with global defaults
- [x]  **System prompt strategy:**
    - *Base persona:* Configurable per tenant (helpful assistant, formal tone, etc.)
    - *Dynamic context injection:* Retrieved QA pairs, conversation history, user language
- [x]  **Context window management:**
    - [x]  Sliding window (last N messages, default 10)
    - [x]  RAG retrieval (top 3 QA pairs by similarity)
    - *Estimated context size:* ~2000 tokens typical

## RAG / Knowledge Base

| Decision | Choice |
| --- | --- |
| **Vector Store** | pgvector (PostgreSQL extension) |
| **Chunk Strategy** | Document-based (one QA pair = one chunk) |
| **Chunk Size** | ~200-500 tokens per QA pair |
| **Retrieval Method** | Similarity (cosine distance) |
| **Top-K** | 3 |

- [x]  **What's in the knowledge base?**
    - *Sources:* Client-provided QA pairs (CSV/JSON import)
    - *Update frequency:* On-demand via admin UI
- [x]  **How is knowledge base populated?**
    - [x]  Manual upload (CSV, JSON, text)
    - [x]  API sync (future: Alchemy integration pattern)

## Guardrails & Safety

- [x]  **Input validation:**
    - [x]  Content filtering (profanity, off-topic detection)
    - [x]  Length limits (10,000 chars max)
    - [x]  Rate limiting (60 req/min per device)
- [x]  **Output validation:**
    - [x]  Hallucination checks (responses grounded in retrieved context only)
    - [x]  Format validation (structured response templates)
    - [ ]  PII filtering (not implemented yet)
- [x]  **Failure modes:**
    - LLM timeout: Return cached response or apologetic fallback
    - LLM error: Try fallback provider, then static message
    - Rate limit hit: 429 with Retry-After header
    - Unexpected output: Log for review, return safe fallback

## Cost Controls

| Metric | Estimate | Limit |
| --- | --- | --- |
| Avg tokens per request | ~1500 input, ~300 output | 4000 max |
| Requests per user/day | ~10 typical | 100 hard cap |
| Monthly cost estimate | $10-30 for 10k queries | $50 budget alert |

- [x]  **Cost optimization strategies:**
    - [x]  Caching responses (24hr TTL, cache hit rate target 30%+)
    - [x]  Using smaller models for simple tasks (Haiku for classification)
    - [x]  Tiered model selection (pattern-based handlers skip LLM entirely)

---

# 6. Critical User Flows

## Primary Flow: User Asks Question

```
1. User sends message (Messenger/Web)
2. Pipeline detects language
3. Pipeline translates to English (if needed)
4. Pipeline checks moderation (profanity, off-topic)
5. Pipeline classifies intent (greeting, farewell, question)
6. If simple intent → return template response (no LLM)
7. If question → retrieve top 3 QA pairs by similarity
8. LLM generates response grounded in retrieved context
9. Response translated back to user's language
10. Response sent to user
11. Exchange saved to memory + observability
```

**Edge cases to handle:**

- No relevant QA pairs found → "I don't have information on that"
- Profanity detected → Warning message, continue
- Off-topic detected → Redirect to scope
- User in handoff mode → Skip processing, notify staff
- Vague question → Ask clarifying question

## Secondary Flow: Admin Edits Prompt

```
1. Admin navigates to Prompt Management
2. Admin selects prompt template (e.g., "system_prompt")
3. Admin edits content in editor
4. Admin clicks "Save as Draft"
5. System creates new version (draft status)
6. Admin clicks "Preview" → test with sample input
7. Admin clicks "Publish"
8. System marks version as active
9. All new conversations use updated prompt
```

## Secondary Flow: Admin Imports QA Pairs

```
1. Admin uploads CSV/JSON file
2. System parses and validates format
3. System shows preview (first 10 rows)
4. Admin confirms import
5. System generates embeddings (background job)
6. System marks QA pairs as "pending_review"
7. Admin reviews and approves in Review Queue
8. Approved pairs become active for retrieval
```

## Forcing Questions

- [x]  **What's the first thing a new user does?**
    - *Action:* Receives greeting message, asks first question
    - *Expected outcome:* Accurate answer in their language within 2 seconds
- [x]  **What's the "aha moment"?**
    - User asks domain-specific question, gets accurate answer instantly in their language
- [x]  **What happens when there's no data yet?**
    - *Empty state:* "I'm still learning. Please check back soon or contact support."

---

# 7. API Surface

## Internal API (Backend ↔ Frontend)

| Endpoint | Method | Purpose | Request Shape | Response Shape |
| --- | --- | --- | --- | --- |
| `/chat` | POST | Send chat message | `{message, device_id, webhook_version}` | `{message, metadata}` |
| `/health` | GET | Health check | - | `{status, components, metrics}` |
| `/qa/pairs` | GET | List QA pairs | `?page, search, status` | `{items[], total, page}` |
| `/qa/pairs` | POST | Create QA pair | `{question, answer, category}` | `{id, ...}` |
| `/qa/import/text` | POST | Bulk import | `{text, skip_duplicates}` | `{count, skipped}` |
| `/prompts` | GET | List prompt templates | `?tenant_id` | `{items[]}` |
| `/prompts/{id}` | PUT | Update prompt | `{content, description}` | `{id, version}` |
| `/prompts/{id}/publish` | POST | Publish version | - | `{id, version, is_active}` |
| `/costs/summary` | GET | Cost dashboard | `?month` | `{total, projection, by_provider}` |
| `/observability/events/stream` | GET | SSE event stream | `?page_id, platform` | SSE stream |

## External API (Messenger Webhook)

| Endpoint | Method | Purpose | Auth | Rate Limit |
| --- | --- | --- | --- | --- |
| `/messenger/webhook` | GET | Verification | Verify token | - |
| `/messenger/webhook` | POST | Incoming messages | Signature validation | Platform-enforced |
| `/messenger/v2/webhook` | POST | V2 pipeline (dev) | Signature validation | Platform-enforced |

## Forcing Questions

- [x]  **Auth mechanism:**
    - [x]  API keys (admin endpoints)
    - [x]  Device ID (anonymous chat users)
    - [x]  Webhook signature (Messenger)
- [x]  **API versioning strategy:**
    - [x]  URL path (`/v1/...`, `/v2/...` for webhook)
    - Internal APIs unversioned (single frontend consumer)
- [x]  **Streaming responses needed?**
    - [x]  Yes: `/observability/events/stream` (SSE)
    - Future: Chat streaming for long responses

---

# 8. Scope Boundaries

## In Scope (v1 / MVP)

| Feature | Priority | Notes |
| --- | --- | --- |
| Multi-tenant data isolation | Must Have | tenant_id on all tables |
| Prompt management UI | Must Have | CRUD + versioning + publish |
| Per-tenant prompt overrides | Must Have | Fallback to global defaults |
| A/B testing for prompts | Should Have | Traffic % split |
| Response template management | Should Have | Greeting, fallback, clarification |
| Tenant admin dashboard | Should Have | QA stats, cost, usage |

## Explicitly Out of Scope (v1)

| Feature | Reason | Future Version? |
| --- | --- | --- |
| Self-service tenant onboarding | Complexity, need manual vetting | v2 |
| Billing integration (Stripe) | MVP is manual invoicing | v2 |
| WhatsApp/LINE/Viber channels | Focus on Messenger + Web first | v2 |
| Voice input/output | Complexity | Maybe |
| Custom LLM fine-tuning | Cost, complexity | Never (RAG is sufficient) |
| On-premise deployment | Support burden | Enterprise tier only |

## Forcing Questions

- [x]  **What's the absolute minimum for first usable release?**
    - Multi-tenant isolation, prompt management, QA management, chat endpoint, basic analytics
- [x]  **What will clients ask for that we're saying no to (for now)?**
    - WhatsApp integration → "Planned for v2, Messenger + Web available now"
    - Custom UI themes → "White-label branding included, custom themes are professional services"
    - Real-time human handoff → "Handoff flagging included, live chat requires separate tool"
- [x]  **What would make this 10x harder to build?**
    - Multi-region deployment (stick to single region)
    - Real-time collaborative editing (stick to single-user admin)
    - Offline-first mobile app (stick to PWA)

---

# 9. Open Questions & Risks

## Open Questions

| Question | Blocks | Owner | Due Date |
| --- | --- | --- | --- |
| Tenant provisioning flow - manual or semi-automated? | Admin UI design | Mark | Jan 25 |
| Prompt editor UI - code editor or rich text? | Frontend implementation | Mark | Jan 25 |
| Per-tenant LLM API keys or shared? | Cost model, security | Mark | Jan 25 |

## Technical Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| V2 response quality not matching V1 (Voiceflow) | H | Prompt management layer allows rapid iteration without deploys |
| LLM provider rate limits at scale | M | Response caching, fallback provider, queue smoothing |
| Multi-tenant data leakage | H | tenant_id enforced at repository layer, integration tests |

## Dependencies

| Dependency | Status | Risk if Delayed |
| --- | --- | --- |
| PALAI codebase as foundation | Confirmed | None - already built |
| PostgreSQL + pgvector | Confirmed | None - already running |
| OpenAI API access | Confirmed | None - already integrated |
| First pilot client (non-PhilRice) | Pending | Delays real-world validation |

---

# 10. Effort Estimation

## Phase Breakdown

| Phase | Scope Summary | Effort (days) | Dependencies |
| --- | --- | --- | --- |
| **Phase 0: Multi-tenant Foundation** | Add tenant_id to models, repository layer enforcement, tenant CRUD | 3 | None |
| **Phase 1: Prompt Management** | PromptTemplate model, versioning, CRUD API, service layer | 3 | Phase 0 |
| **Phase 2: Prompt Admin UI** | Editor page, version history, preview, publish flow | 3 | Phase 1 |
| **Phase 3: Tenant Admin UI** | Tenant dashboard, QA stats, cost view, settings | 2 | Phase 0 |
| **Phase 4: Rebranding & Cleanup** | Remove PhilRice-specific code, configurable branding | 2 | Phase 0 |
| **Phase 5: Demo & Docs** | Demo instance, seed data, video walkthrough, docs | 2 | Phase 4 |

## Effort Summary

| Category | Effort (days) |
| --- | --- |
| Backend | 7 |
| Frontend | 5 |
| AI/ML | 0 (already built) |
| Infrastructure | 1 |
| Testing | Included in phases |
| Documentation | 2 |
| **Total** | **15 days** |

## Confidence Level

- [x]  🟢 High confidence (done this before)

**Confidence notes:** Core architecture proven with PALAI. Multi-tenancy and prompt management are well-understood patterns. Main risk is UI polish time.

## Cost Calculation Reference

| Line Item | Unit | Quantity | Rate | Total |
| --- | --- | --- | --- | --- |
| Development | days | 15 | ₱10,000 | ₱150,000 |
| AI/LLM costs (monthly) | month | 1 | ₱1,500 | ₱1,500 |
| Infrastructure (monthly) | month | 1 | ₱2,000 | ₱2,000 |
| Contingency | % | 20% | - | ₱30,000 |
| **Total Setup** |  |  |  | **₱183,500** |

---

# Approval & Sign-off

| Role | Name | Date | Sign-off |
| --- | --- | --- | --- |
| Technical Lead | Mark | Jan 18, 2025 | ⬜ |
| Product Owner | Mark | Jan 18, 2025 | ⬜ |
| Client (if applicable) | - | - | - |

---

# Appendix

## A. Glossary

| Term | Definition |
|------|------------|
| Instance | A client deployment of Helix |
| QA Pair | A question-answer pair in the knowledge base |
| Prompt Template | A configurable LLM prompt stored in the database |
| Pipeline | The sequence of processors that handle a chat message |
| Processor | A single step in the pipeline (e.g., translation, moderation, retrieval) |
| RAG | Retrieval-Augmented Generation - grounding LLM responses in retrieved context |

## B. Reference Links

| Resource | Description |
|----------|-------------|
| [Deployment Guide](../docs/deployment-guide.md) | How to deploy for a client |
| [Architecture](../00_project_roadmap/02_architecture.md) | System design |
| [Development Guidelines](../00_project_roadmap/00_development_guidelines.md) | TDD workflow |

## C. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Jan 2025 | Database-stored prompts | Enables admin editing, versioning, A/B testing |
| Jan 2025 | Single-tenant per client | Complete isolation, simpler security model |
| Jan 2025 | Product name: Helix | Domain-agnostic, memorable |
| Jan 2026 | Productized from PALAI | Proven architecture, now repeatable |

---

*Last updated: January 2026*
