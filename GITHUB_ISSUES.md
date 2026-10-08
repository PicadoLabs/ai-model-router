# GitHub Issue Specifications for AI Model Router

This document contains ready-to-post GitHub Issue specifications extracted from the project audit. Each issue follows open-source standard formatting, includes precise labels, and marks `good first issue` for community contributors.

---

## Issue 1: [Backend] Replace Deprecated FastAPI on_event Handler with Lifespan Context Manager

**Labels:** `bug`, `backend`, `fastapi`, `good first issue`  
**Priority:** High (P1)  
**Severity:** High  

### Description
The application entrypoint currently uses `@app.on_event("shutdown")` to trigger background connection teardown. In FastAPI, `@app.on_event` is deprecated in favor of standard ASGI `lifespan` context managers.

### Problem / Current Behavior
- Startup triggers runtime deprecation warnings (`DeprecationWarning: on_event is deprecated, use lifespan event handlers instead`).
- Deprecated syntax risks breaking compatibility with future FastAPI versions.

### Expected Behavior
- Connection initialization and teardown should be managed within the `lifespan` context manager in `backend/app/server.py`.
- Application startup should complete with zero deprecation warnings.

### Code Location
- `backend/main.py`
- `backend/app/server.py`

### Proposed Solution
1. Update `lifespan` context manager in `backend/app/server.py`:
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       await init_db()
       yield
       try:
           await close_redis()
       except Exception:
           pass
   ```
2. Remove deprecated `@app.on_event("shutdown")` block from `backend/main.py`.

### Definition of Done
- Application starts cleanly without `DeprecationWarning` logs.
- All unit and integration tests pass (`pytest`).

---

## Issue 2: [Security] Fix Wildcard Origin Configuration in CORS Middleware

**Labels:** `security`, `backend`, `cors`, `good first issue`  
**Priority:** High (P1)  
**Severity:** High  

### Description
The FastAPI server configures `CORSMiddleware` with `allow_origins=["*"]` while setting `allow_credentials=True`.

### Problem / Current Behavior
Modern web browsers reject HTTP responses containing `Access-Control-Allow-Origin: *` when `Access-Control-Allow-Credentials: true` is set. This causes cross-origin request failures in production browser environments.

### Expected Behavior
- CORS middleware should use origin regex patterns (`allow_origin_regex`) or configurable explicit origin lists (`settings.ALLOWED_ORIGINS`).
- Credentials should be permitted safely for local development and authorized production origins.

### Code Location
- `backend/app/server.py`

### Proposed Solution
Update `CORSMiddleware` in `backend/app/server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Definition of Done
- Cross-origin preflight requests succeed from localhost development origins.
- Credentials can be sent with API requests without browser security errors.

---

## Issue 3: [Performance] Replace Database Polling in SSE Traffic Endpoint with In-Memory Event Channel

**Labels:** `enhancement`, `performance`, `backend`, `good first issue`  
**Priority:** Medium (P2)  
**Severity:** Medium  

### Description
The Server-Sent Events (SSE) live traffic stream endpoint `/api/traffic/stream` polls the database every 1.5 seconds when Redis Pub/Sub is unavailable.

### Problem / Current Behavior
- Every connected browser client spawns an infinite loop executing `SELECT ... ORDER BY timestamp DESC LIMIT 1`.
- Multiple concurrent Control Room dashboards create redundant database load.

### Expected Behavior
- Single-instance deployments should use an in-memory `asyncio.Event` or broadcast queue to notify connected SSE streams only when a new decision is persisted.
- Database reads should only execute upon initial stream connection.

### Code Location
- `backend/app/server.py`

### Proposed Solution
1. Introduce an `asyncio.Queue` or listener set in `server.py`.
2. Push new routing decision payloads to active queues upon request completion.
3. Yield event payloads directly from active queues in `stream_live_traffic`.

### Definition of Done
- CPU usage remains low when multiple SSE subscribers are connected.
- Live traffic updates appear instantly upon request completion.

---

## Issue 4: [Database] Add Explicit Indexes to High-Frequency Database Columns

**Labels:** `enhancement`, `database`, `performance`, `good first issue`  
**Priority:** Medium (P2)  
**Severity:** Medium  

### Description
Database models `RequestRecord` and `RoutingDecisionRecord` store routing decisions but lack explicit column indexes on frequently queried fields.

### Problem / Current Behavior
Analytics queries (`/api/analytics`), workspace aggregations, and traffic log exports perform full table scans on unindexed text and datetime columns.

### Expected Behavior
- Frequently filtered columns (`timestamp`, `workspace_id`, `task_type`, `request_id`) should have explicit database indexes.

### Code Location
- `backend/app/storage/models.py`

### Proposed Solution
Add `index=True` or explicit `Index()` definitions to SQLAlchemy model fields:
```python
class RequestRecord(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    request_id = Column(String(64), unique=True, index=True)
    workspace_id = Column(String(64), index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    task_type = Column(String(32), index=True)
```

### Definition of Done
- Migration or table initialization creates indexes on target fields.
- Query execution plans for analytics and export routes utilize index scans.

---

## Issue 5: [Database] Configure SQLite WAL Mode and Connection Timeout for High Concurrency

**Labels:** `enhancement`, `database`, `sqlite`, `good first issue`  
**Priority:** Medium (P2)  
**Severity:** Medium  

### Description
The default SQLite connection initialization in `database.py` does not explicitly enable Write-Ahead Logging (WAL) or set a busy timeout handler.

### Problem / Current Behavior
Concurrent writes from background tasks or parallel request handlers can trigger `sqlite3.OperationalError: database is locked`.

### Expected Behavior
- SQLite connections should automatically enable WAL mode (`PRAGMA journal_mode=WAL`) and a busy timeout of 5000ms.

### Code Location
- `backend/app/storage/database.py`

### Proposed Solution
Attach an event listener to the SQLAlchemy sync engine:
```python
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()
```

### Definition of Done
- SQLite database initializes in WAL mode.
- Concurrent read/write stress tests run without database lock errors.

---

## Issue 6: [Auth] Implement Stale Key Eviction in In-Memory Rate Limiter

**Labels:** `enhancement`, `security`, `memory`, `good first issue`  
**Priority:** Low (P3)  
**Severity:** Low  

### Description
The in-memory rate limiter fallback stores timestamp deques in a `defaultdict(deque)`. Keys for inactive API tokens or IP addresses remain in memory indefinitely.

### Problem / Current Behavior
Over extended operational periods, inactive token keys accumulate in memory, causing minor memory bloat.

### Expected Behavior
- Keys with empty timestamp deques or all entries older than the 60-second window should be evicted automatically.

### Code Location
- `backend/app/auth/rate_limiter.py`

### Proposed Solution
Add an eviction check during limit evaluation or periodic background cleanup:
```python
def _cleanup_stale_keys(self, now: float):
    stale_keys = [
        key for key, timestamps in self._storage.items()
        if not timestamps or timestamps[-1] < (now - 60.0)
    ]
    for key in stale_keys:
        del self._storage[key]
```

### Definition of Done
- Stale keys are removed from memory once timestamps expire past the tracking window.
- In-memory rate limiting functionality remains accurate.

---

## Issue 7: [SDK] Add Async Context Manager Support (`async with`) to Python SDK

**Labels:** `enhancement`, `sdk`, `python`, `good first issue`  
**Priority:** Medium (P2)  
**Severity:** Medium  

### Description
The `AsyncModelRouter` class in the Python SDK supports async methods but lacks context manager implementation (`__aenter__` and `__aexit__`).

### Problem / Current Behavior
Attempting to instantiate the client using `async with AsyncModelRouter(...) as client:` raises an `AttributeError`.

### Expected Behavior
- Developers should be able to use `AsyncModelRouter` with standard Python `async with` blocks.

### Code Location
- `sdk/python/modelrouter/client.py`

### Proposed Solution
Add context manager methods to `AsyncModelRouter`:
```python
async def close(self):
    """Close underlying client resources."""
    pass

async def __aenter__(self):
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.close()
```

### Definition of Done
- `async with AsyncModelRouter(...) as client:` executes cleanly in Python.
- SDK tests pass (`pytest sdk/python/tests/test_python_sdk.py`).

---

## Issue 8: [SDK] Expand Exception Hierarchy for 503 and 504 Status Codes

**Labels:** `enhancement`, `sdk`, `error-handling`, `good first issue`  
**Priority:** Low (P3)  
**Severity:** Low  

### Description
The Python SDK maps non-200 responses to `APIStatusError`, but HTTP 503 (Provider Unavailable) and 504 (Gateway Timeout) share a generic exception class.

### Problem / Current Behavior
SDK consumers must manually inspect `error.status_code` to detect upstream provider outages vs. gateway timeouts.

### Expected Behavior
- Explicit exception classes `ProviderUnavailableError` (HTTP 503) and `GatewayTimeoutError` (HTTP 504) should be available.

### Code Location
- `sdk/python/modelrouter/exceptions.py`
- `sdk/python/modelrouter/client.py`

### Proposed Solution
1. Define specialized exception classes in `exceptions.py`:
   ```python
   class ProviderUnavailableError(APIStatusError):
       """Raised when an upstream AI provider returns 503 Service Unavailable."""

   class GatewayTimeoutError(APIStatusError):
       """Raised when a gateway request times out (HTTP 504)."""
   ```
2. Update `_handle_error_response` mapping in `client.py`.

### Definition of Done
- Status code 503 raises `ProviderUnavailableError`.
- Status code 504 raises `GatewayTimeoutError`.

---

## Issue 9: [Frontend] Implement Code-Splitting with `React.lazy` for Page Components

**Labels:** `enhancement`, `frontend`, `performance`, `good first issue`  
**Priority:** Low (P3)  
**Severity:** Low  

### Description
The React frontend imports all page components synchronously in `App.tsx`, producing a single bundled JavaScript chunk exceeding 750 kB.

### Problem / Current Behavior
- Vite build emits a chunk size warning (`index-CdVzjssr.js is > 500 kB`).
- Initial page load fetches all tab components regardless of which tab is active.

### Expected Behavior
- Secondary pages (`BenchmarksPage`, `Analytics`, `DocsPage`, `SettingsPage`) should be code-split into dynamic chunks.

### Code Location
- `frontend/src/App.tsx`
- `frontend/vite.config.ts`

### Proposed Solution
Wrap secondary page components in `React.lazy()` and `Suspense` inside `App.tsx`:
```tsx
import React, { useState, Suspense } from 'react';

const BenchmarksPage = React.lazy(() => import('./pages/BenchmarksPage').then(m => ({ default: m.BenchmarksPage })));
const DocsPage = React.lazy(() => import('./pages/DocsPage').then(m => ({ default: m.DocsPage })));
const Analytics = React.lazy(() => import('./pages/Analytics').then(m => ({ default: m.Analytics })));
```

### Definition of Done
- Vite build produces multiple smaller asset chunks under 500 kB.
- Frontend navigation works smoothly with loading fallbacks.

---

## Issue 10: [Frontend] Add ARIA Attributes to Interactive Navigation Controls

**Labels:** `enhancement`, `frontend`, `accessibility`, `good first issue`  
**Priority:** Low (P3)  
**Severity:** Low  

### Description
Icon-only controls and dropdown triggers in `Navbar.tsx` lack explicit ARIA accessibility attributes.

### Problem / Current Behavior
Screen reader software cannot properly announce the state or purpose of the theme toggle button and Sections dropdown trigger.

### Expected Behavior
- Interactive elements should feature descriptive `aria-label`, `aria-expanded`, and `aria-haspopup` attributes.

### Code Location
- `frontend/src/components/Navbar.tsx`

### Proposed Solution
Update controls in `Navbar.tsx`:
```tsx
<button
  onClick={toggleTheme}
  aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
  className="..."
>
  ...
</button>

<button
  onClick={() => setSectionsOpen(!sectionsOpen)}
  aria-label="Toggle navigation sections menu"
  aria-expanded={sectionsOpen}
  aria-haspopup="true"
  className="..."
>
  ...
</button>
```

### Definition of Done
- Lighthouse accessibility score increases.
- All interactive controls feature appropriate ARIA metadata.

---

## Issue 11: [CI/CD] Configure Automated GitHub Actions Pipeline Matrix

**Labels:** `enhancement`, `ci-cd`, `devops`, `good first issue`  
**Priority:** Medium (P2)  
**Severity:** Medium  

### Description
The repository lacks an automated GitHub Actions CI workflow to run test suites and verify frontend builds on incoming pull requests.

### Problem / Current Behavior
Pull requests must be tested manually on local environments before merging.

### Expected Behavior
- Every push and pull request should trigger automated pytest testing across Python versions 3.10, 3.11, and 3.12, as well as frontend type-checking and bundling.

### Code Location
- `.github/workflows/ci.yml`

### Proposed Solution
Create `.github/workflows/ci.yml`:
```yaml
name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    name: Backend Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt pytest
      - name: Run Pytest Suite
        run: pytest

  build-frontend:
    name: Frontend Build Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Build Frontend
        run: |
          cd frontend
          npm ci
          npm run build
```

### Definition of Done
- GitHub Actions workflow runs on push/PR.
- Pytest and frontend build jobs pass cleanly in CI.

---

## Issue 12: [Documentation] Add Security Disclosure Policy and Contributing Guide

**Labels:** `documentation`, `oss-standards`, `governance`, `good first issue`  
**Priority:** Low (P3)  
**Severity:** Low  

### Description
Standard open-source governance documents `SECURITY.md` and `CONTRIBUTING.md` are missing from the root repository.

### Problem / Current Behavior
External developers lack formal instructions for contributing code, formatting PRs, or reporting security concerns.

### Expected Behavior
- `SECURITY.md` and `CONTRIBUTING.md` files should be available in the root repository.

### Code Location
- `SECURITY.md`
- `CONTRIBUTING.md`

### Proposed Solution
1. Create `SECURITY.md` detailing supported versions, vulnerability reporting process, and contact channels.
2. Create `CONTRIBUTING.md` outlining repository setup, coding style conventions, PR template guidelines, and test instructions.

### Definition of Done
- `SECURITY.md` and `CONTRIBUTING.md` exist in root directory.
- Governance documentation complies with GitHub open-source community standards.
