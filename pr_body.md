## Summary
Closes #18.

This PR implements production-ready API key authentication, multi-tenant workspace isolation, sliding-window rate limiting, and seeded model catalog presets for modern 2026 model series (including JEV models).

## Changes

### 1. Authentication & Security (\ackend/app/auth/security.py\)
- Added \generate_api_key\ using cryptographically secure random tokens (\mr_live_<hex32>\) with SHA-256 hash indexing.
- Implemented \get_auth_context\ dependency in FastAPI supporting both \X-API-Key\ and \Authorization: Bearer <key>\ headers.
- Safe development fallback: \AUTH_REQUIRED=False\ allows seamless local dev without credentials, while \AUTH_REQUIRED=True\ or supplying a key activates strict token authentication.

### 2. Sliding-Window Rate Limiter (\ackend/app/auth/rate_limiter.py\)
- High-performance sliding-window rate limiter supporting Redis sorted sets with thread-safe in-memory fallback.
- Enforces requests-per-minute (RPM) limits per API key and per workspace.
- Returns HTTP 429 Too Many Requests with standard \Retry-After\, \X-RateLimit-Limit\, \X-RateLimit-Remaining\, and \X-RateLimit-Reset\ response headers.

### 3. Multi-Tenancy & Database Schema (\ackend/app/storage/models.py\, Alembic Migration)
- Added \WorkspaceRecord\ model for workspace-level budget caps, rate limit configs, and lifecycle status.
- Added \ApiKeyRecord\ for hashed token management, prefix masking, expiry, and usage tracking.
- Added \workspace_id\ and \pi_key_id\ foreign references on \RequestRecord\ for tenant traffic audit trails.
- Added Alembic migration \d4c76780952d_add_workspaces_and_api_keys.py\.

### 4. Workspace & API Key Management Endpoints (\ackend/app/api/routes.py\)
- \GET /api/workspaces\, \POST /api/workspaces\, \GET /api/workspaces/{id}\, \PUT /api/workspaces/{id}- \GET /api/keys\ (lists masked key prefixes), \POST /api/keys\ (returns raw key once upon creation), \DELETE /api/keys/{id}\ (revocation)
- Applied authentication and rate limiter checks across \/api/route\, \/api/generate\, and \/api/generate/stream\.

### 5. Automated Tests
- Added unit & integration tests in \ackend/tests/test_auth.py\ and \ackend/tests/test_rate_limiter.py\.
- All 40 unit and end-to-end tests passing.
