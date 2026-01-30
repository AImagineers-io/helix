# Troubleshooting Guide

This guide covers common issues and their solutions when running Helix.

---

## Quick Diagnostics

### Health Check

```bash
curl https://helix-api.example.com/health
```

Expected response:
```json
{"status": "ok", "app_name": "Helix", "version": "1.0.0"}
```

### Check Logs

```bash
# Docker logs
docker logs helix-backend --tail 100

# System logs
journalctl -u helix -n 100
```

---

## Chat Not Responding

### Symptoms

- Chat widget loads but messages get no response
- API returns 500 error
- Response takes too long and times out

### Causes and Solutions

#### 1. OpenAI API Key Invalid

**Check:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Fix:** Update `OPENAI_API_KEY` in environment variables.

#### 2. Database Connection Failed

**Check:**
```bash
docker exec helix-backend python -c "from database.connection import engine; engine.connect()"
```

**Fix:** Verify `DATABASE_URL` is correct and database is accessible.

#### 3. Redis Connection Failed

**Check:**
```bash
redis-cli -h localhost -p 6379 ping
```

**Fix:** Verify Redis is running and `REDIS_URL` is correct.

#### 4. No QA Pairs Loaded

**Check:**
```bash
curl https://helix-api.example.com/qa/pairs \
  -H "X-API-Key: your-key"
```

**Fix:** Import QA pairs using the admin UI or API.

---

## Embeddings Not Generating

### Symptoms

- QA pairs show `embedding_status: pending`
- RAG retrieval returns no results
- Chat responses are generic (not using knowledge base)

### Causes and Solutions

#### 1. OpenAI Embedding API Quota Exceeded

**Check:**
Check OpenAI usage dashboard at https://platform.openai.com/usage

**Fix:** Wait for quota reset or upgrade plan.

#### 2. Background Worker Not Running

**Check:**
```bash
docker exec helix-backend ps aux | grep worker
```

**Fix:** Restart the backend service:
```bash
docker restart helix-backend
```

#### 3. Invalid QA Pair Content

**Check:**
Look for QA pairs with empty questions or answers:
```bash
curl "https://helix-api.example.com/qa/pairs?status=error" \
  -H "X-API-Key: your-key"
```

**Fix:** Delete or update invalid QA pairs.

---

## Facebook Webhook Failing

### Symptoms

- Messages from Messenger not received
- Webhook verification fails
- "Message failed to send" errors in Messenger

### Causes and Solutions

#### 1. Webhook URL Not Accessible

**Check:**
```bash
curl -I https://helix-api.example.com/messenger/webhook
```

**Fix:** Ensure URL is publicly accessible (not behind firewall).

#### 2. Verify Token Mismatch

**Check:** Compare `FB_VERIFY_TOKEN` in your environment with the token configured in Facebook Developer Console.

**Fix:** Update either the environment variable or Facebook settings to match.

#### 3. App Secret Invalid

**Check:**
```bash
# Signature validation will fail silently - check logs
docker logs helix-backend | grep "signature"
```

**Fix:** Update `FB_APP_SECRET` to match Facebook App settings.

#### 4. Page Access Token Expired

**Check:**
```bash
curl "https://graph.facebook.com/me?access_token=$FB_PAGE_ACCESS_TOKEN"
```

**Fix:** Generate new Page Access Token in Facebook Developer Console.

---

## Admin UI Not Loading

### Symptoms

- Blank page on admin URL
- JavaScript console errors
- "Failed to fetch" errors

### Causes and Solutions

#### 1. API URL Misconfigured

**Check:** Browser console for API request URLs.

**Fix:** Update `VITE_API_URL` in frontend environment.

#### 2. CORS Blocking Requests

**Check:** Browser console for CORS errors.

**Fix:** Add frontend URL to `CORS_ORIGINS` in backend config:
```bash
CORS_ORIGINS=https://helix.example.com,http://localhost:3000
```

#### 3. API Key Not Set

**Check:** Network tab for 401 responses.

**Fix:** Ensure `VITE_API_KEY` matches `API_KEY` in backend.

---

## Performance Issues

### Symptoms

- Slow response times (> 5 seconds)
- Timeouts
- High CPU/memory usage

### Causes and Solutions

#### 1. Too Many Concurrent Requests

**Check:**
```bash
# Check connection pool
docker exec helix-backend python -c "from database.connection import engine; print(engine.pool.status())"
```

**Fix:** Increase database pool size or add rate limiting.

#### 2. Large Knowledge Base Without Caching

**Check:**
```bash
redis-cli info memory
```

**Fix:** Ensure Redis is configured and `REDIS_URL` is set.

#### 3. Expensive RAG Queries

**Check:** Response time logs in observability dashboard.

**Fix:**
- Reduce `top_k` in retrieval settings
- Add more specific QA pairs
- Enable response caching

---

## Database Issues

### Connection Refused

```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
1. Check PostgreSQL is running: `systemctl status postgresql`
2. Verify `DATABASE_URL` hostname/port
3. Check firewall rules
4. Verify user credentials

### Migration Errors

```
sqlalchemy.exc.ProgrammingError: relation does not exist
```

**Solutions:**
1. Run migrations: `alembic upgrade head`
2. Check migration history: `alembic history`
3. Reset database (development only): `alembic downgrade base && alembic upgrade head`

### Connection Pool Exhausted

```
sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
```

**Solutions:**
1. Increase pool size in `DATABASE_URL`: `?pool_size=20`
2. Check for connection leaks
3. Reduce concurrent requests

---

## Debug Endpoints

### System Info

```bash
curl https://helix-api.example.com/health
```

### Configuration (Branding)

```bash
curl https://helix-api.example.com/branding
```

### Prompt Templates

```bash
curl https://helix-api.example.com/prompts \
  -H "X-API-Key: your-key"
```

---

## Log Locations

| Component | Location |
|-----------|----------|
| Backend | Docker: `docker logs helix-backend` |
| Frontend | Browser console (F12) |
| Database | `/var/log/postgresql/` |
| Redis | `redis-cli monitor` |
| Nginx | `/var/log/nginx/` |

---

## Getting Help

If issues persist:

1. **Check logs** - Most errors are logged with context
2. **Review configuration** - Verify all environment variables
3. **Test components** - Isolate which component is failing
4. **Check GitHub Issues** - Search for similar problems
5. **Contact support** - Provide logs and configuration

---

*Last updated: January 2026*
