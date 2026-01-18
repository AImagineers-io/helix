# Development Guidelines

## Core Principle: Test-Driven Development (TDD)

**MANDATORY: All development MUST follow TDD**

This project uses strict Test-Driven Development. No feature is considered complete without tests written FIRST.

---

## TDD Workflow

### The Red-Green-Refactor Cycle

```
1. RED    → Write a failing test
2. GREEN  → Write minimum code to pass
3. REFACTOR → Improve code quality
4. REPEAT
```

### Detailed Process

#### 1. Write Test FIRST (RED)

**Before writing any implementation code:**

```python
# Example: tests/integration/test_health_endpoint.py

def test_health_endpoint_returns_200():
    """Test that /health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_endpoint_returns_json():
    """Test that /health returns JSON with status"""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
```

**Run the test - it MUST FAIL:**
```bash
pytest tests/integration/test_health_endpoint.py
# Expected: FAIL (endpoint doesn't exist yet)
```

**This is GOOD** - we've defined what success looks like.

---

#### 2. Implement MINIMUM Code (GREEN)

**Write the simplest code to make the test pass:**

```python
# backend/api/routes.py

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Run the test again:**
```bash
pytest tests/integration/test_health_endpoint.py
# Expected: PASS (both tests green)
```

**Now we have working code with proof it works**

---

#### 3. Refactor (Clean Up)

**Improve code quality WITHOUT changing behavior:**

```python
# After refactor (if needed)
from schemas import HealthResponse

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(status="ok", timestamp=datetime.utcnow())
```

**Run tests again to ensure nothing broke:**
```bash
pytest tests/integration/test_health_endpoint.py
# Expected: STILL PASS
```

**Code is now clean AND proven to work**

---

## Testing Pyramid

### Integration Tests (Primary Focus)

**Write integration tests FIRST** - these test the full flow:

```python
# tests/integration/test_chat_flow.py

def test_user_asks_question_gets_answer():
    """Test complete chat flow end-to-end"""
    # Given: User has a question
    request = {"message": "What is the return policy?", "device_id": "test123"}

    # When: User sends message
    response = client.post("/chat", json=request)

    # Then: System returns an answer
    assert response.status_code == 200
    assert "message" in response.json()
    assert len(response.json()["message"]) > 0
```

**Integration tests verify:**
- API endpoints work
- Services connect properly
- Database queries execute
- Full user flow completes

---

### Unit Tests (Supporting)

**After integration tests pass, add unit tests for complex logic:**

```python
# tests/unit/test_pipeline_processors.py

def test_language_detection():
    """Test language detection processor"""
    processor = LanguageDetectionProcessor()

    assert processor.detect("Hello, how are you?") == "en"
    assert processor.detect("Magandang umaga!") == "tl"
    assert processor.detect("Bonjour!") == "fr"

def test_moderation_filter():
    """Test content moderation"""
    processor = ModerationProcessor()

    result = processor.process("normal question")
    assert result.flagged == False

    result = processor.process("inappropriate content")
    assert result.flagged == True
```

**Unit tests verify:**
- Individual functions work correctly
- Edge cases handled
- Logic is sound

---

## Test Organization

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_chat_flow.py
│   │   ├── test_tenant_isolation.py
│   │   └── test_prompt_management.py
│   └── unit/
│       ├── __init__.py
│       ├── test_pipeline_processors.py
│       ├── test_services.py
│       └── test_utils.py
```

---

## Testing Standards

### Test Naming Convention

```python
def test_<what>_<condition>_<expected_result>():
    """Clear description of what we're testing"""
    pass

# Examples:
def test_health_endpoint_returns_200():
def test_chat_endpoint_requires_device_id():
def test_prompt_versioning_creates_new_version():
def test_tenant_isolation_prevents_cross_access():
```

### Test Structure (Arrange-Act-Assert)

```python
def test_example():
    # Arrange: Set up test data
    request = {"message": "test", "device_id": "123"}

    # Act: Execute the code being tested
    response = client.post("/chat", json=request)

    # Assert: Verify expected outcome
    assert response.status_code == 200
```

---

## Multi-Tenant Testing

### Tenant Isolation Tests

**Critical for Helix** - always test that tenants cannot access each other's data:

```python
# tests/integration/test_tenant_isolation.py

def test_tenant_cannot_access_other_tenant_qa_pairs():
    """Test tenant data isolation"""
    # Arrange: Create QA pairs for two tenants
    tenant_a = create_tenant("Tenant A")
    tenant_b = create_tenant("Tenant B")

    qa_pair = create_qa_pair(tenant_id=tenant_a.id, question="Test Q", answer="Test A")

    # Act: Try to access Tenant A's data as Tenant B
    response = client.get(
        f"/qa/pairs/{qa_pair.id}",
        headers={"X-Tenant-ID": str(tenant_b.id)}
    )

    # Assert: Access denied
    assert response.status_code == 404  # Or 403, depending on design

def test_tenant_qa_pairs_filtered_by_tenant_id():
    """Test that QA pair listing respects tenant boundaries"""
    tenant_a = create_tenant("Tenant A")
    tenant_b = create_tenant("Tenant B")

    # Create QA pairs for both tenants
    create_qa_pair(tenant_id=tenant_a.id, question="A's Question", answer="A's Answer")
    create_qa_pair(tenant_id=tenant_b.id, question="B's Question", answer="B's Answer")

    # Get QA pairs for Tenant A
    response = client.get("/qa/pairs", headers={"X-Tenant-ID": str(tenant_a.id)})

    # Should only see Tenant A's data
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["question"] == "A's Question"
```

---

## Running Tests

### Using Helix Test CLI (Recommended)

```bash
# Run all tests (backend + frontend)
python helix.py test

# Run backend tests only
python helix.py test backend

# Run frontend tests only
python helix.py test frontend

# Run backend unit tests only
python helix.py test unit

# Run backend integration tests only
python helix.py test integration

# Check backend health
python helix.py health

# Show version
python helix.py version
```

**Benefits:**
- Runs tests locally regardless of deployment environment
- Includes coverage reports by default
- Color-coded output for easy reading
- Consistent testing workflow for TDD

### Direct Test Commands (Advanced)

```bash
# Backend - all tests
cd backend
source venv/bin/activate
DATABASE_URL=sqlite:///:memory: pytest -v

# Backend - specific test file
DATABASE_URL=sqlite:///:memory: pytest tests/integration/test_health_endpoint.py -v

# Backend - with coverage
DATABASE_URL=sqlite:///:memory: pytest --cov=. --cov-report=term-missing -v

# Frontend - all tests
cd frontend
npm test -- --run

# Frontend - with coverage
npm test -- --run --coverage
```

---

## Git Workflow

### Commit Convention

```bash
# Format: <type>: <description>

# Types:
test: Add failing test for health endpoint
feat: Implement health endpoint to pass tests
refactor: Extract health check to separate module
fix: Correct health endpoint response format
docs: Update API documentation
```

### Workflow Steps

1. **Write test** → Commit
```bash
git add tests/
git commit -m "test: add failing test for prompt versioning"
```

2. **Implement code** → Commit
```bash
git add backend/
git commit -m "feat: implement prompt versioning (tests pass)"
```

3. **Refactor** → Commit
```bash
git add backend/
git commit -m "refactor: extract prompt service methods"
```

---

## Code Quality Standards

### Python (Backend)

- **Formatting**: Black (line length 88)
- **Linting**: Ruff
- **Type hints**: Required for function signatures
- **Docstrings**: Required for public functions

```python
def process_message(message: str, device_id: str, tenant_id: int) -> dict:
    """
    Process user message and return response.

    Args:
        message: User's question
        device_id: Unique device identifier
        tenant_id: Tenant organization identifier

    Returns:
        dict: Response with answer and metadata
    """
    pass
```

### TypeScript (Frontend)

- **Formatting**: Prettier
- **Linting**: ESLint
- **Types**: Strict TypeScript, no `any`

```typescript
interface ChatRequest {
  message: string;
  device_id: string;
  tenant_id?: number;
}

async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  // Implementation
}
```

---

## Definition of Done

A feature is DONE when:

- Integration tests written FIRST
- Tests were RED (failed initially)
- Implementation makes tests GREEN (pass)
- Code refactored for quality
- Tests still GREEN after refactor
- Unit tests added for complex logic
- Tenant isolation verified (if applicable)
- Code reviewed (if applicable)
- Documentation updated
- Committed with proper message

---

## Production-Critical Components

### DO NOT MODIFY Without Approval

Some components are production-critical:

| Component | Reason |
|-----------|--------|
| `messenger_webhook.py` | **PRODUCTION** - Facebook's configured webhook endpoint |
| Multi-tenant middleware | Data isolation - security critical |
| Authentication handlers | Security critical |

### Webhook Safety Rules

**The V1 Messenger webhook is accessed by Facebook in production. Any changes can break the live chatbot for real users.**

#### What to do instead:

1. **Use V2 for development** - Develop new features on V2 webhook
2. **Test thoroughly** - Integration tests for all webhook changes
3. **Gradual migration** - When ready, reconfigure Facebook to use V2

---

## Anti-Patterns to AVOID

### Writing Code Before Tests
```python
# WRONG: Implementation first
@app.get("/prompts")
def list_prompts():
    return {"prompts": []}

# Then writing test after - proves nothing
def test_prompts():
    assert True
```

### Tests That Always Pass
```python
# WRONG: Test doesn't verify behavior
def test_prompts():
    response = client.get("/prompts")
    assert True  # This proves nothing!
```

### Testing Implementation Details
```python
# WRONG: Testing internal variable names
def test_service():
    service = PromptService()
    assert service._internal_cache == {}
```

### Ignoring Tenant Isolation
```python
# WRONG: Not checking tenant boundaries
def test_get_qa_pair():
    response = client.get("/qa/pairs/1")
    assert response.status_code == 200
    # Missing: verify tenant_id filtering!
```

---

## TDD Mindset

### Think in This Order:

1. **What should it do?** → Write test
2. **Does it fail?** → Run test (should be RED)
3. **Make it work** → Write minimal code
4. **Does it pass?** → Run test (should be GREEN)
5. **Make it better** → Refactor
6. **Still works?** → Run test (should stay GREEN)

### Remember:

- Tests are **specifications** - they define correct behavior
- RED is good - it means you're testing something new
- GREEN is earned - every green test is a small victory
- Refactor with confidence - tests protect you
- **Tenant isolation is non-negotiable** - always test boundaries

---

## Testing Tools

### Python (Backend)

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **httpx** - Async HTTP client for testing
- **factory_boy** - Test data factories

### TypeScript (Frontend)

- **Vitest** - Testing framework (Vite-native)
- **Testing Library** - UI component testing
- **MSW** - Mock Service Worker for API mocking

---

## Summary

**TDD = Better Code**

- Write test FIRST → Know what success looks like
- Watch it FAIL → Verify you're testing something real
- Write code → Make it pass
- Refactor → Improve quality safely
- Repeat → Build with confidence

**Every feature follows: TEST → RED → CODE → GREEN → REFACTOR**

**No exceptions. No shortcuts. TDD always.**
