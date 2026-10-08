# Comprehensive Project Audit & OSS Enhancement Roadmap

> **Project:** AI Model Router (v1.2.0)  
> **Repository:** `PicadoLabs/ai-model-router`  
> **Audit Date:** October 2026  
> **Status:** Active Open-Source Production Standard Audit  

---

## Executive Summary

This document presents a comprehensive, line-by-line codebase audit of the **AI Model Router** platform across the backend FastAPI gateway, router scoring engine, Thompson Sampling bandit RL, provider adapters, Python SDK, React/Vite Control Room frontend, Typer CLI, and storage models. 

Each issue is categorized by domain, assigned an OSS severity level, detailed with file paths and line references, and accompanied by a concrete resolution specification.

---

## Table of Contents

1. [High Priority Architectural & Runtime Issues](#1-high-priority-architectural--runtime-issues)
2. [Backend Engine & Storage Optimizations](#2-backend-engine--storage-optimizations)
3. [SDK & API Compatibility Enhancements](#3-sdk--api-compatibility-enhancements)
4. [Frontend Bundle & Performance Optimizations](#4-frontend-bundle--performance-optimizations)
5. [Open-Source (OSS) Standard Compliance & CI/CD](#5-open-source-oss-standard-compliance--cicd)
6. [Summary Matrix & Implementation Order](#6-summary-matrix--implementation-order)

---

## 1. High Priority Architectural & Runtime Issues

### ISSUE-01: Deprecated FastAPI `on_event("shutdown")` Lifecycle Handler
- **Severity:** High (Deprecation / Future Breaking Change)
- **File:** `backend/main.py` ([main.py](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/backend/main.py#L8-L10))
- **Root Cause:** Uses `@app.on_event("shutdown")` which is deprecated in FastAPI in favor of the standard ASGI `lifespan` context manager. Additionally, `close_redis()` is invoked without explicit import.
- **Impact:** Triggers runtime deprecation warnings on application startup and may break in future FastAPI releases.
- **Recommended Fix:**
  Move connection teardown into the `lifespan` manager in `backend/app/server.py`:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      await init_db()
      yield
      await close_redis()
  ```
  Remove `@app.on_event("shutdown")` from `backend/main.py`.

---

### ISSUE-02: CORS Middleware Configuration Standard Violation
- **Severity:** High (Browser Security Compliance)
- **File:** `backend/app/server.py` ([server.py](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/backend/app/server.py#L35-L41))
- **Root Cause:** `allow_origins=["*"]` is combined with `allow_credentials=True`. Modern web browsers reject wildcard origins when credentials are included (`Access-Control-Allow-Origin: *` cannot be used with credentials).
- **Impact:** Third-party web applications making authenticated requests with credentials will encounter CORS preflight failures in production browsers.
- **Recommended Fix:**
  Use configurable origin patterns via `settings.ALLOWED_ORIGINS` (defaulting to local dev ports):
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.ALLOWED_ORIGINS or ["http://localhost:5173", "http://localhost:3000"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

---

### ISSUE-03: Polling Fallback in Live SSE Traffic Stream
- **Severity:** Medium (Performance & CPU Overhead)
- **File:** `backend/app/server.py` ([server.py](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/backend/app/server.py#L52-L82))
- **Root Cause:** `/api/traffic/stream` polls the database every 1.5 seconds (`while True` with `asyncio.sleep(1.5)` and `SELECT ... LIMIT 1`) when Redis Pub/Sub is inactive.
- **Impact:** Generates unnecessary DB query load when multiple Control Room dashboards are open concurrently.
- **Recommended Fix:**
  Implement an in-memory `asyncio.Event` or broadcast channel for single-instance deployments, reserving database queries only for initial client connection state.

---

## 2. Backend Engine & Storage Optimizations

### ISSUE-04: Missing Database Indexes on High-Frequency Query Columns
- **Severity:** Medium (Database Performance at Scale)
- **File:** `backend/app/storage/models.py` ([models.py](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/backend/app/storage/models.py))
- **Root Cause:** `RequestRecord` and `RoutingDecisionRecord` store historical logs but lack explicit indexes on `timestamp`, `workspace_id`, and `task_type`.
- **Impact:** Analytics aggregations (`/api/analytics`), workspace billing queries, and traffic exports require full table scans as request volume grows past 100K rows.
- **Recommended Fix:**
  Add SQLAlchemy `index=True` or explicit `Index()` definitions:
  ```python
  class RequestRecord(Base):
      __tablename__ = "requests"
      id = Column(Integer, primary_primary_key=True)
      request_id = Column(String(64), unique=True, index=True)
      workspace_id = Column(String(64), index=True, nullable=True)
      timestamp = Column(DateTime, default=datetime.utcnow, index=True)
      task_type = Column(String(32), index=True)
  ```

---

### ISSUE-05: SQLite WAL Mode & Connection Busy Timeout Configuration
- **Severity:** Medium (Concurrency & Locking)
- **File:** `backend/app/storage/database.py` ([database.py](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/backend/app/storage/database.py))
- **Root Cause:** Default SQLite connection initialization does not explicitly set `PRAGMA journal_mode=WAL` or `PRAGMA busy_timeout=5000`.
- **Impact:** High concurrent traffic or parallel background tasks can trigger `sqlite3.OperationalError: database is locked`.
- **Recommended Fix:**
  Attach an `on_connect` listener to the SQLAlchemy engine:
  ```python
  @event.listens_for(engine.sync_engine, "connect")
  def set_sqlite_pragma(dbapi_connection, connection_record):
      cursor = dbapi_connection.cursor()
      cursor.execute("PRAGMA journal_mode=WAL")
      cursor.execute("PRAGMA busy_timeout=5000")
      cursor.close()
  ```

---

### ISSUE-06: In-Memory Rate Limiter Stale Key Eviction
- **Severity:** Low (Memory Optimization)
- **File:** `backend/app/auth/rate_limiter.py` ([rate_limiter.py](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/backend/app/auth/rate_limiter.py))
- **Root Cause:** The fallback in-memory rate limiter stores request timestamp deques in a `defaultdict(deque)`. Keys for inactive API tokens or IP addresses remain in memory indefinitely.
- **Impact:** Slight gradual memory growth in long-running standalone deployments without Redis.
- **Recommended Fix:**
  Implement a periodic cleanup loop or LRU cache eviction mechanism for keys where all timestamps are older than the 60-second window.

---

## 3. SDK & API Compatibility Enhancements

### ISSUE-07: Python SDK Async Context Manager Support
- **Severity:** Medium (Developer Experience)
- **File:** `sdk/python/modelrouter/client.py`
- **Root Cause:** `AsyncModelRouter` provides async methods (`chat.completions.create`), but does not implement `__aenter__` and `__aexit__` for clean resource teardown.
- **Impact:** Developers using `async with AsyncModelRouter(...) as client:` will receive an `AttributeError`.
- **Recommended Fix:**
  Add async context manager methods to `AsyncModelRouter`:
  ```python
  async def __aenter__(self):
      return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
      await self.close()
  ```

---

### ISSUE-08: HTTP Status Error Mapping Granularity in SDK
- **Severity:** Low (Robustness)
- **File:** `sdk/python/modelrouter/exceptions.py`
- **Root Cause:** `APIStatusError` catches non-200 responses, but HTTP 503 (Provider Unavailable) and HTTP 504 (Gateway Timeout) share a generic base exception without specialized subclass attributes.
- **Impact:** SDK consumers cannot easily differentiate between routing failures (HTTP 422) and upstream provider outages (HTTP 503) without parsing raw status codes.
- **Recommended Fix:**
  Add specialized exception subclasses: `ProviderUnavailableError` (503) and `GatewayTimeoutError` (504).

---

## 4. Frontend Bundle & Performance Optimizations

### ISSUE-09: Single JavaScript Chunk Size Exceeding 500 kB
- **Severity:** Low (Performance Optimization)
- **File:** `frontend/vite.config.ts` & `frontend/src/App.tsx` ([App.tsx](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/frontend/src/App.tsx))
- **Root Cause:** All pages (`Dashboard`, `Playground`, `BenchmarksPage`, `Analytics`, `DocsPage`, `StartPage`) are imported synchronously at top level, bundling the entire application into a single `764 kB` JavaScript asset.
- **Impact:** Increases initial page load time on slower network connections.
- **Recommended Fix:**
  Implement dynamic imports with `React.lazy()` and `Suspense` in `App.tsx`:
  ```tsx
  const BenchmarksPage = React.lazy(() => import('./pages/BenchmarksPage'));
  const DocsPage = React.lazy(() => import('./pages/DocsPage'));
  const Analytics = React.lazy(() => import('./pages/Analytics'));
  ```

---

### ISSUE-10: Accessibility (a11y) ARIA Labels on Interactive Controls
- **Severity:** Low (OSS Accessibility Standard)
- **File:** `frontend/src/components/Navbar.tsx` ([Navbar.tsx](file:///c:/Users/vardh/Documents/Projects/PicadoLabs/AI%20Model%20Router/frontend/src/components/Navbar.tsx))
- **Root Cause:** Some icon-only buttons (such as theme toggle and dropdown triggers) lack explicit `aria-label` or `aria-expanded` attributes.
- **Impact:** Screen readers cannot properly describe icon-only interactive controls to visually impaired users.
- **Recommended Fix:**
  Add explicit `aria-label="Toggle theme"` and `aria-expanded={sectionsOpen}` attributes across all navigation controls.

---

## 5. Open-Source (OSS) Standard Compliance & CI/CD

### ISSUE-11: CI/CD GitHub Actions Pipeline Configuration
- **Severity:** Medium (OSS Infrastructure)
- **File:** `.github/workflows/ci.yml` (New File Required)
- **Root Cause:** Project lacks a automated `.github/workflows/ci.yml` matrix testing across Python 3.10, 3.11, and 3.12 on Linux, macOS, and Windows.
- **Impact:** Pull requests cannot be automatically validated for regression or build breaks before merging.
- **Recommended Fix:**
  Create `.github/workflows/ci.yml`:
  ```yaml
  name: Model Router CI

  on:
    push:
      branches: [ main ]
    pull_request:
      branches: [ main ]

  jobs:
    test-backend:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          python-version: ["3.10", "3.11", "3.12"]
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: ${{ matrix.python-version }}
        - run: pip install -r backend/requirements.txt pytest
        - run: pytest

    build-frontend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-node@v4
          with:
            node-version: 20
        - run: cd frontend && npm ci && npm run build
  ```

---

### ISSUE-12: Missing Security Disclosure Policy & Contributing Guide
- **Severity:** Low (OSS Governance)
- **Files:** `SECURITY.md`, `CONTRIBUTING.md` (New Files Required)
- **Root Cause:** Standard open-source governance files are missing from the root repository.
- **Impact:** External contributors lack clear guidelines for submitting code changes or reporting security issues responsibly.
- **Recommended Fix:**
  Add standard `SECURITY.md` (reporting email, vulnerability disclosure timeline) and `CONTRIBUTING.md` (development setup, PR checklist, code formatting).

---

## 6. Summary Matrix & Implementation Order

| Issue ID | Module / Component | Severity | Description | Priority |
|---|---|---|---|---|
| **ISSUE-01** | Backend Gateway | **High** | Deprecated `@app.on_event("shutdown")` handler in `main.py` | P1 |
| **ISSUE-02** | Security & CORS | **High** | Wildcard CORS origins combined with `allow_credentials=True` | P1 |
| **ISSUE-03** | SSE Streaming | **Medium** | DB polling fallback in SSE endpoint every 1.5s | P2 |
| **ISSUE-04** | Database Models | **Medium** | Missing indexes on `timestamp`, `workspace_id`, `task_type` | P2 |
| **ISSUE-05** | SQLite Engine | **Medium** | SQLite WAL mode and busy timeout not explicitly set | P2 |
| **ISSUE-06** | Auth / Limiter | **Low** | In-memory rate limiter deque cleanup for stale keys | P3 |
| **ISSUE-07** | Python SDK | **Medium** | Async context manager (`async with`) support in SDK | P2 |
| **ISSUE-08** | Python SDK | **Low** | Granular exception mapping for 503 / 504 status codes | P3 |
| **ISSUE-09** | Frontend Build | **Low** | Code-splitting heavy pages (`React.lazy`) to reduce bundle size | P3 |
| **ISSUE-10** | Frontend UI | **Low** | ARIA labels for icon-only buttons and navigation controls | P3 |
| **ISSUE-11** | CI/CD Pipeline | **Medium** | Automated GitHub Actions workflow for multi-OS/Python testing | P2 |
| **ISSUE-12** | OSS Governance | **Low** | Standard `SECURITY.md` and `CONTRIBUTING.md` documentation | P3 |

---

*This document serves as the master issues backlog for elevating Model Router to enterprise-grade open-source production standards.*
