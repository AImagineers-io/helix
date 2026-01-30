# Post-Deployment Verification

This document provides a checklist and automated script for verifying a successful Helix deployment.

---

## Quick Verification

Run the automated verification script:

```bash
./scripts/verify_deployment.sh https://helix-api.example.com
```

---

## Manual Verification Checklist

### 1. Health Check

```bash
curl -s https://helix-api.example.com/health | jq .
```

**Expected:**
```json
{
  "status": "ok",
  "app_name": "Your App Name",
  "version": "1.0.0"
}
```

**Pass criteria:**
- [ ] Returns 200 OK
- [ ] Status is "ok"
- [ ] App name matches configuration

---

### 2. Branding Endpoint

```bash
curl -s https://helix-api.example.com/branding | jq .
```

**Expected:**
```json
{
  "app_name": "Your App Name",
  "app_description": "Your description",
  "bot_name": "Your Bot",
  "logo_url": "https://...",
  "primary_color": "#3B82F6"
}
```

**Pass criteria:**
- [ ] Returns 200 OK
- [ ] App name is correct
- [ ] Logo URL is accessible (if set)
- [ ] No default/placeholder values

---

### 3. Chat Endpoint

```bash
curl -s -X POST https://helix-api.example.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "device_id": "verify-test"}' | jq .
```

**Expected:**
```json
{
  "message": "Hello! How can I help you today?",
  "conversation_id": "...",
  "metadata": {...}
}
```

**Pass criteria:**
- [ ] Returns 200 OK
- [ ] Response message is not empty
- [ ] Response is relevant to input

---

### 4. Admin API Authentication

```bash
# Without API key (should fail)
curl -s https://helix-api.example.com/prompts | jq .

# With API key (should succeed)
curl -s https://helix-api.example.com/prompts \
  -H "X-API-Key: your-api-key" | jq .
```

**Pass criteria:**
- [ ] Without key: Returns 401 Unauthorized
- [ ] With key: Returns 200 OK with prompts list

---

### 5. Facebook Webhook (If Enabled)

```bash
# Verification challenge
curl -s "https://helix-api.example.com/messenger/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"
```

**Expected:** Returns `test123`

**Pass criteria:**
- [ ] Returns the challenge value
- [ ] No error response

---

### 6. Frontend Accessibility

```bash
curl -s -I https://helix.example.com | head -5
```

**Pass criteria:**
- [ ] Returns 200 OK
- [ ] Content-Type is text/html
- [ ] No redirect errors

---

### 7. SSL/TLS Verification

```bash
curl -vI https://helix-api.example.com 2>&1 | grep -E "(SSL|certificate|expire)"
```

**Pass criteria:**
- [ ] Certificate is valid
- [ ] Not expired
- [ ] Issued to correct domain

---

### 8. Database Connectivity

```bash
# Via API endpoint that requires database
curl -s https://helix-api.example.com/prompts \
  -H "X-API-Key: your-key" | jq '.[] | .name' | head -3
```

**Pass criteria:**
- [ ] Returns data from database
- [ ] No connection errors

---

### 9. Redis Connectivity

```bash
# Cache headers indicate Redis is working
curl -sI https://helix-api.example.com/branding | grep -i etag
```

**Pass criteria:**
- [ ] ETag header present
- [ ] Consistent on multiple requests

---

### 10. Response Time Check

```bash
# Measure response time
time curl -s https://helix-api.example.com/health > /dev/null
```

**Pass criteria:**
- [ ] Health check < 500ms
- [ ] Chat response < 5s

---

## Automated Verification Script

The `verify_deployment.sh` script performs all checks automatically:

```bash
./scripts/verify_deployment.sh https://helix-api.example.com [API_KEY] [FB_VERIFY_TOKEN]
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more checks failed |
| 2 | Invalid arguments |

### Example Output

```
Helix Deployment Verification
============================
Target: https://helix-api.example.com

[PASS] Health check
[PASS] Branding endpoint
[PASS] Chat endpoint
[PASS] Admin authentication
[SKIP] Facebook webhook (no token provided)
[PASS] Response time (234ms)

Results: 5 passed, 0 failed, 1 skipped
```

---

## Smoke Test Sequence

After deployment, run these tests in order:

1. **Infrastructure** - Health, SSL, DNS
2. **API** - Branding, authentication
3. **Core functionality** - Chat, QA retrieval
4. **Integrations** - Facebook (if enabled)
5. **Performance** - Response times

---

## Rollback Criteria

Rollback the deployment if:

- Health check fails
- Chat endpoint returns errors
- SSL certificate is invalid
- Response times exceed 10 seconds
- Database connectivity fails

---

## Post-Verification

After successful verification:

1. Monitor error rates for 30 minutes
2. Check observability dashboard
3. Verify logs show no errors
4. Notify stakeholders of completion

---

*Last updated: January 2026*
