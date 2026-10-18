"""
Tests for CORS configuration and settings in backend/app.
Verifies localhost/loopback support, explicit production origin handling,
OPTIONS preflight requests, credentials compliance, and settings parsing.
"""
from typing import List, Optional
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import Settings, get_settings
from app.server import app as real_app, setup_cors


def create_cors_test_app(allowed_origins: Optional[List[str]] = None) -> FastAPI:
    """Helper to create an isolated FastAPI app using setup_cors from app.server."""
    app = FastAPI(title="CORS Test App")
    setup_cors(app, allowed_origins=allowed_origins)

    @app.get("/api/test")
    async def get_test():
        return {"status": "ok"}

    @app.post("/api/test")
    async def post_test():
        return {"status": "created"}

    return app


# ============================================================================
# 0. Real Application CORS Middleware Tests
# ============================================================================

@pytest.mark.asyncio
async def test_real_app_cors_configuration():
    """Verify that the actual production FastAPI app has CORSMiddleware configured via setup_cors and functions properly."""
    cors_middlewares = [m for m in real_app.user_middleware if m.cls is CORSMiddleware]
    assert len(cors_middlewares) == 1, "CORSMiddleware must be registered on the real application"
    mw = cors_middlewares[0]
    assert mw.kwargs["allow_credentials"] is True
    assert mw.kwargs["allow_origin_regex"] == r"http://(localhost|127\.0\.0\.1)(:\d+)?"
    assert mw.kwargs["allow_methods"] == ["*"]
    assert mw.kwargs["allow_headers"] == ["*"]

    transport = ASGITransport(app=real_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Localhost request to real app
        res_lh = await client.get("/docs", headers={"Origin": "http://localhost:3000"})
        assert res_lh.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert res_lh.headers.get("access-control-allow-credentials") == "true"

        # Unauthorized request to real app
        res_evil = await client.get("/docs", headers={"Origin": "https://unauthorized-attacker.com"})
        assert res_evil.headers.get("access-control-allow-origin") is None


# ============================================================================
# 1. Pydantic Settings Parsing Tests
# ============================================================================

def test_settings_allowed_origins_default():
    """Verify ALLOWED_ORIGINS defaults to an empty list with Field(default_factory=list)."""
    s1 = Settings()
    s2 = Settings()
    assert s1.ALLOWED_ORIGINS == [], "Default ALLOWED_ORIGINS should be an empty list"
    assert s2.ALLOWED_ORIGINS == [], "Default ALLOWED_ORIGINS should be an empty list"
    # Ensure instances do not share the same mutable list object
    assert s1.ALLOWED_ORIGINS is not s2.ALLOWED_ORIGINS, "Field(default_factory=list) must produce distinct lists"


def test_settings_allowed_origins_json_parsing(monkeypatch):
    """Verify ALLOWED_ORIGINS correctly parses a JSON-array formatted environment variable."""
    expected = ["https://app.example.com", "https://dashboard.example.com"]
    monkeypatch.setenv("ALLOWED_ORIGINS", '["https://app.example.com", "https://dashboard.example.com"]')
    get_settings.cache_clear()
    try:
        s = Settings()
        assert s.ALLOWED_ORIGINS == expected, f"Expected {expected}, got {s.ALLOWED_ORIGINS}"

        cached_settings = get_settings()
        assert cached_settings.ALLOWED_ORIGINS == expected
    finally:
        get_settings.cache_clear()


def test_settings_cache_isolation(monkeypatch):
    """Verify that settings cache clear ensures no pollution across test environments."""
    monkeypatch.setenv("ALLOWED_ORIGINS", '["https://isolated.example.com"]')
    get_settings.cache_clear()
    s_override = get_settings()
    assert s_override.ALLOWED_ORIGINS == ["https://isolated.example.com"]

    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    get_settings.cache_clear()
    s_default = get_settings()
    assert s_default.ALLOWED_ORIGINS == []


# ============================================================================
# 2. Localhost and Loopback IP Origin Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("origin", [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1",
])
async def test_cors_localhost_and_loopback_allowed(origin: str):
    """Verify HTTP localhost and 127.0.0.1 origins (with or without port) are permitted with credentials."""
    app = create_cors_test_app(allowed_origins=[])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/test", headers={"Origin": origin})
        assert res.status_code == 200
        # Must reflect the specific requesting origin, never wildcard "*"
        assert res.headers.get("access-control-allow-origin") == origin
        assert res.headers.get("access-control-allow-origin") != "*"
        # Must explicitly allow credentials
        assert res.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", [
    "https://localhost:3000",
    "https://localhost",
    "https://127.0.0.1:8000",
    "https://127.0.0.1",
])
async def test_cors_https_localhost_disallowed(origin: str):
    """Verify HTTPS localhost and 127.0.0.1 origins are rejected by default (regex strictly matches http://)."""
    app = create_cors_test_app(allowed_origins=[])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/test", headers={"Origin": origin})
        assert res.status_code == 200
        # Disallowed origins must not receive Access-Control-Allow-Origin header
        assert res.headers.get("access-control-allow-origin") is None


# ============================================================================
# 3. Explicitly Configured Production Origins Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cors_configured_production_origins_allowed():
    """Verify explicitly configured HTTPS production origins are authorized with credentials."""
    allowed = ["https://app.example.com", "https://admin.example.com"]
    app = create_cors_test_app(allowed_origins=allowed)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for origin in allowed:
            res = await client.get("/api/test", headers={"Origin": origin})
            assert res.status_code == 200
            assert res.headers.get("access-control-allow-origin") == origin
            assert res.headers.get("access-control-allow-origin") != "*"
            assert res.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", [
    "https://malicious.example.com",
    "https://evil-site.org",
    "http://example.com",
    "https://app.example.com.attacker.com",
])
async def test_cors_unauthorized_external_origins_rejected(origin: str):
    """Verify unconfigured external origins are rejected and receive no CORS allow-origin header."""
    allowed = ["https://app.example.com"]
    app = create_cors_test_app(allowed_origins=allowed)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/test", headers={"Origin": origin})
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") is None


# ============================================================================
# 4. OPTIONS Preflight Request Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cors_options_preflight_allowed_origin():
    """Verify OPTIONS preflight succeeds with correct CORS headers for configured production origin."""
    allowed = ["https://app.example.com"]
    app = create_cors_test_app(allowed_origins=allowed)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.options(
            "/api/test",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") == "https://app.example.com"
        assert res.headers.get("access-control-allow-origin") != "*"
        assert res.headers.get("access-control-allow-credentials") == "true"

        # Verify allowed methods and headers in preflight response
        allow_methods = res.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods or "*" in allow_methods

        allow_headers = res.headers.get("access-control-allow-headers", "").lower()
        assert "authorization" in allow_headers or "*" in allow_headers


@pytest.mark.asyncio
async def test_cors_options_preflight_localhost():
    """Verify OPTIONS preflight succeeds with correct CORS headers for localhost development origin."""
    app = create_cors_test_app(allowed_origins=[])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.options(
            "/api/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert res.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_options_preflight_unauthorized_rejected():
    """Verify OPTIONS preflight from unauthorized origin fails CORS headers."""
    allowed = ["https://app.example.com"]
    app = create_cors_test_app(allowed_origins=allowed)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.options(
            "/api/test",
            headers={
                "Origin": "https://attacker.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        # Unauthorized preflight must either be 400 or omit access-control-allow-origin
        assert res.headers.get("access-control-allow-origin") is None
