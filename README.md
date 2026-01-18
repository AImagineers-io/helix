# Helix

**White-label RAG Chatbot Platform**

Helix helps government agencies and research institutions deploy AI-powered Q&A chatbots so they can serve citizens 24/7 in their own language, without expensive call centers or hallucinating answers.

## Overview

Helix is a retrieval-augmented generation (RAG) chatbot platform that answers questions from your curated knowledge base. Key features include:

- **Multi-language support** - Detects language, processes in English, responds in user's language
- **Multi-channel deployment** - Web widget, Facebook Messenger, REST API
- **Admin dashboard** - QA management, prompt editing, analytics, issue triage
- **Cost tracking** - Built-in budget alerts and usage monitoring
- **White-label ready** - Customizable branding per client

## Documentation

| Document | Description |
| --- | --- |
| [Productization Framework](01_documentation/helix-productization-framework.md) | Product readiness checklist, commercials, and conversion status |
| [Technical Product Brief](01_documentation/helix-technical-product-brief.md) | Architecture, data model, API surface, and implementation plan |

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL + pgvector |
| Cache | Redis |
| Frontend | React + Vite + TypeScript |
| Deployment | Docker Compose |

## Status

🟡 **In Development** - Converting from PALAI (PhilRice) to productized platform

## License

Proprietary - AImagineers

---

*Built by AImagineers*
