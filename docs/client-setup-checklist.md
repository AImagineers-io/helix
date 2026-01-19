# Helix Client Setup Checklist

Step-by-step checklist for deploying a new Helix instance for a client.

---

## Pre-Deployment (Week -1)

### Client Requirements Gathering

- [ ] **Knowledge Base**
  - [ ] Confirm minimum 200 QA pairs available
  - [ ] Verify QA content is in CSV/Excel format
  - [ ] Identify subject matter expert for QA review (2-4 hours/week)
  - [ ] Confirm content language(s) needed

- [ ] **Branding Assets**
  - [ ] Logo (PNG/SVG, transparent background preferred)
  - [ ] Primary brand color (hex code)
  - [ ] Preferred bot name
  - [ ] App name for white-labeling

- [ ] **Domain and Access**
  - [ ] Domain name or subdomain for deployment (e.g., chat.client.com)
  - [ ] DNS management access
  - [ ] Confirm domain ownership

- [ ] **Integration Requirements**
  - [ ] Facebook Page access (if Messenger needed)
  - [ ] Facebook App creation approval
  - [ ] Other channels needed (WhatsApp, Web widget only, etc.)

- [ ] **Budget and Approvals**
  - [ ] LLM API costs approved (~$10-30/month for 10k queries)
  - [ ] Hosting costs approved (if applicable)
  - [ ] Decision maker identified for weekly check-ins

---

## Setup Phase (Days 1-3)

### Repository Setup

- [ ] **Fork Repository**
  - [ ] Fork `helix` repository to client's GitHub/GitLab org
  - [ ] Clone forked repository to deployment server
  - [ ] Create `deploy/client-name` branch

### Environment Configuration

- [ ] **Database Setup**
  - [ ] Create PostgreSQL database `clientname_helix_db`
  - [ ] Create database user with secure password
  - [ ] Grant privileges to user
  - [ ] Enable `pgvector` extension
  - [ ] Verify connection from deployment server

- [ ] **Environment Variables (.env)**
  - [ ] Copy `.env.example` to `.env`
  - [ ] Set `DATABASE_URL` with connection string
  - [ ] Set `REDIS_URL` (or use Docker Redis)
  - [ ] Generate and set `API_KEY` (`openssl rand -hex 32`)
  - [ ] Generate and set `SECRET_KEY` (`openssl rand -hex 32`)
  - [ ] Set `APP_NAME` (client's branded name)
  - [ ] Set `APP_DESCRIPTION` (client's description)
  - [ ] Set `BOT_NAME` (chatbot's name)
  - [ ] Set `LOGO_URL` (hosted logo URL)
  - [ ] Set `PRIMARY_COLOR` (client's brand color)
  - [ ] Set `DEBUG=false` for production
  - [ ] Set `LOG_LEVEL=INFO`

- [ ] **LLM Provider Keys**
  - [ ] Obtain OpenAI API key (client or AImagineers account)
  - [ ] Set `OPENAI_API_KEY`
  - [ ] (Optional) Obtain Anthropic API key for fallback
  - [ ] (Optional) Obtain Google Translate API key for multilingual

### Database Initialization

- [ ] **Run Migrations**
  ```bash
  cd 02_backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  alembic upgrade head
  ```

- [ ] **Seed Initial Data**
  ```bash
  python helix.py seed prompts
  ```

- [ ] **Verify Schema**
  - [ ] Confirm `prompt_templates` table exists
  - [ ] Confirm `prompt_versions` table exists
  - [ ] Verify initial prompts are seeded

---

## Deployment Phase (Days 4-7)

### Docker Compose Deployment

- [ ] **Update Configuration**
  - [ ] Edit `docker-compose.yml` with correct ports
  - [ ] Verify service names (`client-backend`, `client-frontend`, `client-redis`)
  - [ ] Confirm volume mounts for persistence
  - [ ] Set restart policies to `unless-stopped`

- [ ] **Build and Deploy**
  ```bash
  docker-compose build
  docker-compose up -d
  docker-compose ps  # Verify all services running
  ```

- [ ] **Health Checks**
  - [ ] Backend: `curl http://localhost:8014/health`
  - [ ] Frontend: `curl http://localhost:8015`
  - [ ] Redis: `docker-compose exec client-redis redis-cli ping`

### DNS and Tunnel Setup

- [ ] **Cloudflare Tunnel**
  - [ ] Install `cloudflared` on deployment server
  - [ ] Login to Cloudflare: `cloudflared tunnel login`
  - [ ] Create tunnel: `cloudflared tunnel create client-helix`
  - [ ] Configure `~/.cloudflared/config.yml` with frontend and backend routes
  - [ ] Create DNS CNAME records for tunnel
  - [ ] Start tunnel: `cloudflared tunnel run client-helix`
  - [ ] Install as system service: `cloudflared service install`

- [ ] **DNS Verification**
  - [ ] Frontend resolves: `nslookup chat.client.com`
  - [ ] Backend API resolves: `nslookup chat-api.client.com`
  - [ ] SSL certificate active (Cloudflare auto-provisions)

- [ ] **Public Access Test**
  - [ ] Frontend loads: `https://chat.client.com`
  - [ ] Backend health: `https://chat-api.client.com/health`
  - [ ] No CORS errors in browser console

---

## Facebook Messenger Integration (Days 8-10, if applicable)

### Facebook App Setup

- [ ] **Create Facebook App**
  - [ ] Go to https://developers.facebook.com
  - [ ] Create new app (Business type)
  - [ ] Add "Messenger" product
  - [ ] Generate Page Access Token
  - [ ] Copy App Secret

- [ ] **Configure Environment**
  - [ ] Set `FB_PAGE_ACCESS_TOKEN` in `.env`
  - [ ] Set `FB_APP_SECRET` in `.env`
  - [ ] Generate custom `FB_VERIFY_TOKEN` (random string)
  - [ ] Set `ENABLE_MESSENGER=true`
  - [ ] Restart backend: `docker-compose restart client-backend`

- [ ] **Configure Webhook**
  - [ ] In Facebook App Dashboard → Messenger → Settings
  - [ ] Click "Add Callback URL"
  - [ ] URL: `https://chat-api.client.com/messenger/webhook`
  - [ ] Verify Token: (from `.env` `FB_VERIFY_TOKEN`)
  - [ ] Subscribe to fields: `messages`, `messaging_postbacks`
  - [ ] Verify webhook successfully

- [ ] **Subscribe Page to App**
  - [ ] In Facebook App Dashboard → Messenger → Settings
  - [ ] Select client's Facebook Page
  - [ ] Click "Subscribe" to connect page to app

- [ ] **Test Messenger Integration**
  - [ ] Send test message to Facebook Page
  - [ ] Verify bot responds
  - [ ] Check backend logs for webhook events
  - [ ] Test various message types (text, emojis)

---

## Content Import Phase (Days 11-14)

### QA Pair Import

- [ ] **Prepare QA Data**
  - [ ] Convert client QA to CSV format
  - [ ] Verify CSV headers: `question,answer,category`
  - [ ] Remove duplicates
  - [ ] Review for quality (typos, incomplete answers)

- [ ] **Import via Admin UI**
  - [ ] Navigate to `https://chat.client.com/admin/qa-pairs`
  - [ ] Click "Import"
  - [ ] Upload CSV file
  - [ ] Review import preview
  - [ ] Confirm import
  - [ ] Verify QA pairs appear in admin dashboard

- [ ] **Generate Embeddings**
  - [ ] Verify OpenAI API key is working
  - [ ] Trigger embedding generation (backend job)
  - [ ] Monitor logs for embedding progress
  - [ ] Verify `has_embedding=true` for imported QA pairs

- [ ] **Test Retrieval**
  - [ ] Ask sample questions in chat widget
  - [ ] Verify correct QA pairs are retrieved
  - [ ] Check relevance of answers
  - [ ] Adjust prompts if needed

### Prompt Customization

- [ ] **Review Default Prompts**
  - [ ] Navigate to `https://chat.client.com/admin/prompts`
  - [ ] Review `system_prompt` content
  - [ ] Review `retrieval_prompt` content
  - [ ] Check if any client-specific language needed

- [ ] **Customize Prompts (if needed)**
  - [ ] Edit system prompt with client's tone/style
  - [ ] Update retrieval prompt if special formatting needed
  - [ ] Create new version
  - [ ] Publish new version
  - [ ] Test changes in chat widget

---

## Testing and QA Phase (Days 15-17)

### Functional Testing

- [ ] **Web Widget Testing**
  - [ ] Load chat widget on desktop
  - [ ] Load chat widget on mobile
  - [ ] Test various question types
  - [ ] Verify response quality
  - [ ] Check multilingual support (if enabled)
  - [ ] Test error handling (invalid input, LLM timeout)

- [ ] **Messenger Testing (if applicable)**
  - [ ] Send messages from different user accounts
  - [ ] Test conversation flow
  - [ ] Verify message threading
  - [ ] Test "Talk to Staff" handoff (if enabled)
  - [ ] Check message delivery consistency

- [ ] **Admin Dashboard Testing**
  - [ ] Login to admin panel
  - [ ] View QA pairs list
  - [ ] Edit QA pair
  - [ ] View analytics dashboard
  - [ ] Export conversation logs
  - [ ] Test prompt management

### Performance Testing

- [ ] **Load Testing**
  - [ ] Send 10 concurrent chat requests
  - [ ] Verify average response time < 3 seconds
  - [ ] Check Redis cache hit rate (should increase over time)
  - [ ] Monitor backend CPU/memory usage

- [ ] **Monitoring Setup**
  - [ ] Verify logs are rotating properly
  - [ ] Set up alerts for service downtime (optional)
  - [ ] Configure LLM cost alerts (optional)
  - [ ] Test backup/restore procedure

---

## Client Handoff Phase (Days 18-21)

### Documentation

- [ ] **Create Client-Specific Docs**
  - [ ] Admin user guide (how to manage QA pairs)
  - [ ] How to edit prompts
  - [ ] How to view analytics
  - [ ] Escalation procedures for issues

- [ ] **Credentials Handoff**
  - [ ] Share admin panel URL and login
  - [ ] Document where `.env` is stored
  - [ ] Share database connection details (if client manages DB)
  - [ ] Document Cloudflare tunnel setup

### Training

- [ ] **Admin Training Session**
  - [ ] Walkthrough of admin dashboard
  - [ ] How to add/edit QA pairs
  - [ ] How to review conversation logs
  - [ ] How to edit prompts
  - [ ] When to contact support

- [ ] **Support Handoff**
  - [ ] Define support channels (email, Slack, tickets)
  - [ ] Set SLA expectations
  - [ ] Document common troubleshooting steps

### Go-Live Checklist

- [ ] **Final Verification**
  - [ ] All QA pairs imported and tested
  - [ ] Prompts customized to client's needs
  - [ ] Messenger webhook working (if applicable)
  - [ ] SSL certificate valid
  - [ ] Monitoring/alerts configured
  - [ ] Client training completed
  - [ ] Documentation delivered

- [ ] **Go-Live Approval**
  - [ ] Client approves bot responses
  - [ ] Client approves branding
  - [ ] Client confirms go-live date
  - [ ] Announce launch (if applicable)

---

## Post-Launch (Week 4+)

### Monitoring and Optimization

- [ ] **Week 1 Check-in**
  - [ ] Review conversation logs
  - [ ] Identify gaps in knowledge base
  - [ ] Measure deflection rate (target: 70%+)
  - [ ] Check average response time (target: < 2s)
  - [ ] Review LLM costs

- [ ] **Week 2 Check-in**
  - [ ] Add missing QA pairs based on user questions
  - [ ] Refine prompts based on response quality
  - [ ] Review analytics and usage patterns
  - [ ] Optimize cache settings if needed

- [ ] **Week 4 Check-in**
  - [ ] Measure success metrics (deflection rate, satisfaction)
  - [ ] Plan next iteration (new features, integrations)
  - [ ] Collect client feedback
  - [ ] Document lessons learned

---

## Emergency Contacts

| Issue | Contact |
|-------|---------|
| Server down | DevOps: ops@aimagineers.io |
| LLM API issues | Platform: support@aimagineers.io |
| Client requests | Account Manager: [assign] |
| Bug reports | Development: dev@aimagineers.io |

---

## Common Issues

### Bot not responding

1. Check backend health: `curl https://chat-api.client.com/health`
2. Check backend logs: `docker-compose logs client-backend`
3. Verify OpenAI API key is valid
4. Check database connection

### Messenger webhook not working

1. Verify webhook URL in Facebook App settings
2. Check `FB_VERIFY_TOKEN` matches
3. Test webhook manually: `curl https://chat-api.client.com/messenger/webhook`
4. Review Facebook App logs for errors

### Low response quality

1. Review prompts for clarity
2. Check if QA pairs have embeddings (`has_embedding=true`)
3. Verify retrieval is finding relevant QA pairs
4. Adjust `retrieval_prompt` to improve context usage

---

*Last updated: January 2026*
*Helix v0.1.0*
