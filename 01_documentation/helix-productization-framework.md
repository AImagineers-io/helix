# Helix Productization Framework

Internal checklist for tracking Helix product readiness.

## Product Name

**Helix** - AImagineers Chatbot Deployment Framework

---

## Problem Clarity

- [x]  **What problem does this solve for clients?**
    - Organizations with knowledge bases need accurate, scalable Q&A without expensive support staff.
- [x]  **What problem does this solve for us?**
    - Eliminates bespoke chatbot development. One codebase, configured per client.
- [x]  **Pain points addressed:**
    - Staff overwhelmed with repetitive inquiries
    - Inconsistent answers across channels
    - Support costs that scale linearly with demand

---

## Solution Boundaries

- [x]  **What it does:**
    - RAG chatbot grounded in client's knowledge base
    - Multi-language (auto-detects, responds in user's language)
    - Multi-channel (Web widget, Messenger, API)
    - Cost tracking and budget alerts
    - Admin dashboard for QA and prompt management
- [x]  **What it does NOT do:**
    - Not a general-purpose LLM (grounded in knowledge base only)
    - Not a live chat replacement
    - Not a content authoring tool
    - Not multi-tenant (one instance per client)
- [x]  **Deployment model:**
    - White-label, single-tenant per client, configured via environment variables

---

## Standard Deliverables

What we ship per client:

- [x]  Helix instance (Docker deployment)
- [x]  Chat widget (embeddable + standalone)
- [x]  Facebook Messenger integration (if needed)
- [x]  Admin dashboard (QA, prompts, analytics)
- [x]  REST API for integrations
- [x]  QA import tools (CSV, JSON, text)
- [x]  Cost monitoring dashboard
- [x]  White-label branding

**Demo assets:**
- [x]  Screenshots
- [x]  Architecture diagram
- [x]  Live demo instance

---

## Success Metrics (Client-Facing)

What we promise:

| Timeline | Target |
|----------|--------|
| 30 days | Chatbot live with 500+ QA pairs |
| 60 days | 70%+ inquiry deflection |
| 90 days | Cost per query < $0.01 |

---

## Pricing

| Item | Amount |
|------|--------|
| Setup | ₱150,000 |
| Monthly retainer | ₱25,000 |

**Excluded (additional cost):**
- QA content creation
- Additional language support
- WhatsApp/LINE/Viber integrations
- On-premise deployment

---

## Client Requirements

What we need from clients:

- QA pairs (CSV/Excel, 200+ recommended)
- Facebook Page access (if Messenger needed)
- Brand assets (logo, colors, bot name)
- SME availability (2-4 hrs/week during onboarding)
- LLM API budget (~$10-30/month)

---

## Internal Value Prop

> Helix lets us deploy production-ready chatbots for any client in days, not weeks. One codebase, configured per client.

---

## Readiness Status

| Area | Status |
|------|--------|
| Core Framework | ✅ Complete |
| White-label Config | ✅ Complete |
| Prompt Management | ✅ Complete |
| Admin Dashboard | ✅ Complete |
| Demo Instance | ✅ Complete |
| Documentation | 🟡 In Progress |

**Overall: Ready for deployments**

---

## Conversion Checklist (from PALAI)

**Origin:** PALAI (PhilRice deployment)
**Status:** ✅ Complete

- [x] Client-specific branding removed
- [x] All values moved to environment config
- [x] Generic prompts (no domain-specific content)
- [x] Demo seed data available
- [x] Single-tenant deployment model working

---

## Deployment Readiness

- [x] Repo tagged as v0.5.0
- [x] Docker configs tested
- [x] Demo instance deployed
- [x] Deployment guide written
- [x] Client setup checklist documented

---

## Pricing Reference

| Item | Amount |
|------|--------|
| Setup (one-time) | ₱150,000 |
| Monthly retainer | ₱25,000 |
| Customization | ₱2,500/hr |
| Priority support add-on | ₱5,000/mo |

---

*Last updated: January 2026*
