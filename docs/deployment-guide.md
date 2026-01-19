# Helix Deployment Guide

Complete guide for deploying a new Helix instance using Docker Compose.

---

## Prerequisites

Before deploying Helix, ensure you have:

- [x] Docker and Docker Compose installed
- [x] PostgreSQL database server (or use Docker Compose for local DB)
- [x] Domain name and DNS access
- [x] Cloudflare account (for tunnel deployment)
- [x] OpenAI API key (or Anthropic API key)
- [x] Facebook Page and App (if using Messenger integration)

---

## Architecture Overview

Helix consists of three main services:

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
│                            │                                 │
│                ┌───────────▼──────────┐                      │
│                │  Cloudflare Tunnel   │                      │
│                │   (aimph-tunnel)     │                      │
│                └───────────┬──────────┘                      │
│                            │                                 │
│          ┌─────────────────┴─────────────────┐               │
│          │                                   │               │
│    ┌─────▼──────┐                  ┌────────▼─────┐         │
│    │  Frontend  │                  │   Backend    │         │
│    │   :8015    │                  │    :8014     │         │
│    │(React/Vite)│                  │   (FastAPI)  │         │
│    └────────────┘                  └──────┬───────┘         │
│                                           │                 │
│                              ┌────────────▼────────┐         │
│                              │  helix-redis :6381  │         │
│                              └─────────────────────┘         │
│                                           │                 │
│                              ┌────────────▼────────┐         │
│                              │   PostgreSQL        │         │
│                              │   helix_db :5432    │         │
│                              └─────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Fork and Clone Repository

```bash
# Fork the repository on GitHub/GitLab first, then clone your fork
git clone https://github.com/YOUR_ORG/helix.git
cd helix

# Create a new branch for your deployment config
git checkout -b deploy/your-client-name
```

---

## Step 2: Configure Environment Variables

Copy the example environment file and configure for your deployment:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

### Database Configuration

```bash
# PostgreSQL (Production)
DATABASE_URL=postgresql://helix_user:your_password@db01:5432/helix_db

# OR SQLite (Development/Demo)
DATABASE_URL=sqlite:///./helix.db
```

### LLM Provider Keys

```bash
# OpenAI (Primary)
OPENAI_API_KEY=sk-your-openai-api-key

# Anthropic (Fallback - optional)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Google Translate (Optional for multilingual support)
GOOGLE_TRANSLATE_API_KEY=your-google-api-key
```

### Application Branding

```bash
# White-label configuration
APP_NAME=Your Company AI Assistant
APP_DESCRIPTION=AI-powered Q&A chatbot for your organization
BOT_NAME=YourBot
LOGO_URL=https://your-domain.com/logo.png
PRIMARY_COLOR=#3B82F6
```

### Security

```bash
# Generate secure random keys
API_KEY=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)

# Add to .env
API_KEY=your_generated_api_key
SECRET_KEY=your_generated_secret_key
```

### Frontend Build Arguments

```bash
VITE_API_URL=https://your-api-domain.com
VITE_API_KEY=your_frontend_api_key
VITE_APP_NAME=Your Company AI
```

### Facebook Messenger (Optional)

```bash
FB_PAGE_ACCESS_TOKEN=your_facebook_page_token
FB_VERIFY_TOKEN=your_custom_verify_token
FB_APP_SECRET=your_facebook_app_secret
```

### Feature Flags

```bash
ENABLE_VARIETY_PROCESSOR=false  # Domain-specific (set false for generic)
ENABLE_MESSENGER=true            # Enable if using Facebook Messenger
ENABLE_ANALYTICS=true             # Enable observability dashboard
```

---

## Step 3: Database Setup

### Option A: PostgreSQL (Production)

1. **Create Database and User:**

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE helix_db;

-- Create user
CREATE USER helix_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE helix_db TO helix_user;

-- Enable pgvector extension
\c helix_db
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Run Migrations:**

```bash
# Install backend dependencies
cd 02_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### Option B: SQLite (Development/Demo)

SQLite databases are created automatically - no setup required.

```bash
DATABASE_URL=sqlite:///./helix.db
```

---

## Step 4: Seed Initial Data

Seed the database with default prompts:

```bash
# Seed default prompts
python helix.py seed prompts

# OR seed demo data (for testing)
python helix.py seed demo
```

Verify seeding:

```bash
# Connect to database
psql -U helix_user -d helix_db

# Check prompts
SELECT name, prompt_type FROM prompt_templates;
```

---

## Step 5: Docker Compose Deployment

### Update docker-compose.yml

Edit `docker-compose.yml` to match your configuration:

```yaml
version: '3.8'

services:
  # Backend API
  helix-backend:
    build:
      context: ./02_backend
      dockerfile: Dockerfile
    container_name: helix-backend
    ports:
      - "8014:8000"  # External:Internal
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://helix-redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - API_KEY=${API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - APP_NAME=${APP_NAME}
      - BOT_NAME=${BOT_NAME}
    depends_on:
      - helix-redis
    restart: unless-stopped

  # Frontend
  helix-frontend:
    build:
      context: ./03_frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=${VITE_API_URL}
        - VITE_API_KEY=${VITE_API_KEY}
        - VITE_APP_NAME=${VITE_APP_NAME}
    container_name: helix-frontend
    ports:
      - "8015:3000"
    restart: unless-stopped

  # Redis Cache
  helix-redis:
    image: redis:7-alpine
    container_name: helix-redis
    ports:
      - "6381:6379"
    restart: unless-stopped
```

### Build and Start Services

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Step 6: Cloudflare Tunnel Setup

### Install cloudflared

```bash
# Ubuntu/Debian
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Or use Docker
docker pull cloudflare/cloudflared:latest
```

### Configure Tunnel

1. **Login to Cloudflare:**

```bash
cloudflared tunnel login
```

2. **Create Tunnel:**

```bash
cloudflared tunnel create helix-tunnel
```

3. **Configure Tunnel (`~/.cloudflared/config.yml`):**

```yaml
tunnel: helix-tunnel-id
credentials-file: /path/to/helix-tunnel-credentials.json

ingress:
  # Frontend
  - hostname: helix.your-domain.com
    service: http://localhost:8015

  # Backend API
  - hostname: helix-api.your-domain.com
    service: http://localhost:8014

  # Catch-all rule (required)
  - service: http_status:404
```

4. **Configure DNS:**

```bash
# Create DNS CNAME records
cloudflared tunnel route dns helix-tunnel helix.your-domain.com
cloudflared tunnel route dns helix-tunnel helix-api.your-domain.com
```

5. **Start Tunnel:**

```bash
# Run as service
cloudflared tunnel run helix-tunnel

# Or install as system service
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

---

## Step 7: Health Checks

Verify deployment:

```bash
# Backend health
curl https://helix-api.your-domain.com/health

# Expected response:
# {"status":"ok","name":"Your Company AI","version":"0.1.0"}

# Frontend (visit in browser)
open https://helix.your-domain.com

# Check logs
docker-compose logs -f helix-backend
docker-compose logs -f helix-frontend
```

---

## Step 8: Import QA Pairs

Import your knowledge base:

```bash
# Via Admin UI
# Navigate to https://helix.your-domain.com/admin/qa-pairs
# Click "Import" and upload CSV

# Via API
curl -X POST https://helix-api.your-domain.com/qa/import/csv \
  -H "X-API-Key: your_api_key" \
  -F "file=@knowledge_base.csv"

# CSV format:
# question,answer,category
# "What are your hours?","We're open 9am-5pm weekdays","General"
```

---

## Step 9: Facebook Messenger Integration (Optional)

If using Messenger:

1. **Configure Webhook in Facebook Developer Portal:**

   - Callback URL: `https://helix-api.your-domain.com/messenger/webhook`
   - Verify Token: (from `.env` `FB_VERIFY_TOKEN`)
   - Subscribe to: `messages`, `messaging_postbacks`

2. **Test Webhook:**

```bash
curl -X GET "https://helix-api.your-domain.com/messenger/webhook?hub.mode=subscribe&hub.verify_token=your_verify_token&hub.challenge=CHALLENGE"

# Should return: CHALLENGE
```

3. **Subscribe Page to App:**

   - In Facebook Developer Console
   - Select your Page
   - Click "Subscribe"

---

## Step 10: Monitoring and Maintenance

### Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f helix-backend

# Last 100 lines
docker-compose logs --tail=100 helix-backend
```

### Database Backups

```bash
# PostgreSQL backup
pg_dump -U helix_user helix_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U helix_user helix_db < backup_20260119.sql
```

### Update Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Run any new migrations
cd 02_backend
source venv/bin/activate
alembic upgrade head
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check environment variables
docker-compose config

# Check database connection
docker-compose exec helix-backend python -c "from database.connection import engine; print(engine.url)"

# View detailed logs
docker-compose logs helix-backend --tail=100
```

### Frontend Build Fails

```bash
# Check build args
cat 03_frontend/.env.production

# Rebuild with no cache
docker-compose build --no-cache helix-frontend
```

### Tunnel Connection Issues

```bash
# Check tunnel status
cloudflared tunnel info helix-tunnel

# Test local services
curl http://localhost:8014/health
curl http://localhost:8015
```

### Database Connection Refused

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Check PostgreSQL accepts connections
psql -U helix_user -d helix_db -c "SELECT 1;"

# Verify DATABASE_URL in .env
```

---

## Production Checklist

Before going live:

- [ ] Change all default passwords and API keys
- [ ] Set `DEBUG=false` in `.env`
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS (Cloudflare handles this automatically)
- [ ] Configure database backups
- [ ] Set up monitoring and alerts
- [ ] Test chat functionality end-to-end
- [ ] Import production QA pairs
- [ ] Test Messenger webhook (if enabled)
- [ ] Configure log rotation
- [ ] Document any custom configuration

---

## Support

For issues or questions:

- GitHub Issues: https://github.com/your-org/helix/issues
- Documentation: https://github.com/your-org/helix/docs
- Email: support@your-domain.com

---

*Last updated: January 2026*
*Helix v0.1.0*
