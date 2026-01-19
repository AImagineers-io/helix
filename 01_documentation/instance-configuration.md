# Instance Configuration Guide

This guide explains how to configure a new Helix instance for a client deployment.

## Overview

Helix uses environment variables for all client-specific configuration, enabling white-label deployment without code changes. Each client gets their own dedicated instance with customized branding and features.

## Quick Start

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your client-specific values

3. Start the application:
   ```bash
   docker-compose up -d
   ```

## Configuration Sections

### Database

```env
DATABASE_URL=postgresql://user:password@host:5432/database
```

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |

### Redis

```env
REDIS_URL=redis://localhost:6379
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection string |

### Security

```env
SECRET_KEY=your-secret-key-here
API_KEY=your-admin-api-key
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes* | Dev default | Secret key for signing tokens |
| `API_KEY` | No | None | API key for admin endpoints |

*Required for production deployments.

### Branding

Configure the instance's visual identity and chatbot persona:

```env
APP_NAME=Client Bot
APP_DESCRIPTION=AI assistant for Client Inc
BOT_NAME=Aria
LOGO_URL=https://client.com/logo.png
PRIMARY_COLOR=#FF5733
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `Helix` | Application name in UI and API docs |
| `APP_DESCRIPTION` | No | `AI-powered Q&A chatbot` | Short description |
| `BOT_NAME` | No | `Helix Assistant` | Chatbot persona name |
| `LOGO_URL` | No | None | URL to logo image |
| `PRIMARY_COLOR` | No | `#3B82F6` | Primary brand color (hex) |

### Feature Flags

Enable or disable functionality per instance:

```env
ENABLE_VARIETY_PROCESSOR=true
ENABLE_MESSENGER=true
ENABLE_ANALYTICS=true
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_VARIETY_PROCESSOR` | No | `true` | Enable variety-specific processing |
| `ENABLE_MESSENGER` | No | `true` | Enable Facebook Messenger integration |
| `ENABLE_ANALYTICS` | No | `true` | Enable analytics and observability |

### Application Settings

```env
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://client.com,https://app.client.com
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CORS_ORIGINS` | No | `localhost:3000` | Comma-separated allowed origins |

## API Endpoints

### Health Check

```
GET /health
```

Returns instance health and configuration:

```json
{
  "status": "ok",
  "app_name": "Client Bot",
  "version": "0.1.0"
}
```

### Branding

```
GET /branding
```

Returns branding configuration for frontend:

```json
{
  "app_name": "Client Bot",
  "app_description": "AI assistant for Client Inc",
  "bot_name": "Aria",
  "logo_url": "https://client.com/logo.png",
  "primary_color": "#FF5733"
}
```

## Deployment Checklist

Before deploying a new instance:

- [ ] Database created and accessible
- [ ] Redis available (or disabled if not needed)
- [ ] `SECRET_KEY` set to unique, secure value
- [ ] `APP_NAME` customized for client
- [ ] `BOT_NAME` customized for client persona
- [ ] `LOGO_URL` points to client logo (if available)
- [ ] `PRIMARY_COLOR` matches client brand
- [ ] `CORS_ORIGINS` includes client domains
- [ ] Feature flags configured as needed
- [ ] LLM API keys configured (OpenAI/Anthropic)
- [ ] Messenger integration configured (if enabled)

## Example: Client Deployment

For a client "Acme Corp" with a blue brand color:

```env
# Branding
APP_NAME=Acme Assistant
APP_DESCRIPTION=AI-powered support for Acme Corp
BOT_NAME=Ada
LOGO_URL=https://acme.com/assets/logo.png
PRIMARY_COLOR=#1E40AF

# Features
ENABLE_VARIETY_PROCESSOR=false
ENABLE_MESSENGER=true
ENABLE_ANALYTICS=true

# CORS
CORS_ORIGINS=https://acme.com,https://support.acme.com
```

## Troubleshooting

### Configuration Not Loading

1. Verify `.env` file exists in project root
2. Check environment variables are exported (for non-Docker deployments)
3. Restart the application after changes

### CORS Errors

1. Add frontend domain to `CORS_ORIGINS`
2. Include both `http://` and `https://` if needed
3. Restart backend after changes

### Branding Not Updating

1. Clear browser cache
2. Check `/branding` endpoint returns expected values
3. Verify environment variables are set correctly
