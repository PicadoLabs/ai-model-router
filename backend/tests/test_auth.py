import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.storage.database import init_db
from app.auth.security import generate_api_key, hash_api_key
from app.config.settings import get_settings

settings = get_settings()


@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()


@pytest.mark.asyncio
async def test_api_key_generation_and_hashing():
    raw_key, key_hash, prefix = generate_api_key()
    assert raw_key.startswith("mr_live_")
    assert len(key_hash) == 64  # SHA-256 hex digest
    assert prefix.startswith("mr_live_")
    assert hash_api_key(raw_key) == key_hash


@pytest.mark.asyncio
async def test_workspace_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List initial workspaces
        res = await client.get("/api/workspaces")
        assert res.status_code == 200
        workspaces = res.json()
        assert any(w["id"] == "default" for w in workspaces)

        # 2. Create new workspace with unique id
        import uuid
        test_ws_id = f"ws-eng-{uuid.uuid4().hex[:6]}"
        ws_payload = {
            "id": test_ws_id,
            "name": "Engineering Team",
            "description": "Workspace for core backend engineers",
            "daily_budget": 50.0,
            "monthly_budget": 500.0,
            "rate_limit_rpm": 60,
        }
        create_res = await client.post("/api/workspaces", json=ws_payload)
        assert create_res.status_code == 200
        created = create_res.json()
        assert created["id"] == test_ws_id
        assert created["name"] == "Engineering Team"

        # 3. Get single workspace
        get_res = await client.get(f"/api/workspaces/{test_ws_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "Engineering Team"

        # 4. Update workspace
        update_res = await client.put(
            f"/api/workspaces/{test_ws_id}",
            json={"description": "Updated engineering description", "rate_limit_rpm": 100},
        )
        assert update_res.status_code == 200
        assert update_res.json()["rate_limit_rpm"] == 100
        assert update_res.json()["rate_limit_rpm"] == 100


@pytest.mark.asyncio
async def test_api_key_lifecycle_and_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create API key
        key_payload = {
            "name": "Production Service Key",
            "workspace_id": "default",
            "rate_limit_rpm": 120,
        }
        res_create = await client.post("/api/keys", json=key_payload)
        assert res_create.status_code == 200
        key_data = res_create.json()
        assert "key" in key_data
        raw_key = key_data["key"]
        key_id = key_data["id"]

        # 2. List keys (raw key must NOT be leaked in list)
        res_list = await client.get("/api/keys")
        assert res_list.status_code == 200
        keys = res_list.json()
        listed_key = next((k for k in keys if k["id"] == key_id), None)
        assert listed_key is not None
        assert "key" not in listed_key
        assert listed_key["key_prefix"].startswith("mr_live_")

        # 3. Authenticate with valid X-API-Key header
        route_res = await client.post(
            "/api/route",
            json={"prompt": "Calculate prime numbers in Rust", "policy": "balanced"},
            headers={"X-API-Key": raw_key},
        )
        assert route_res.status_code == 200
        assert "decision" in route_res.json()

        # 4. Authenticate with Authorization: Bearer <key>
        gen_res = await client.post(
            "/api/generate",
            json={"prompt": "Say hello in python", "policy": "balanced"},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert gen_res.status_code == 200
        assert "response" in gen_res.json()

        # 5. Test invalid API key
        invalid_res = await client.post(
            "/api/route",
            json={"prompt": "Test invalid key"},
            headers={"X-API-Key": "mr_live_invalidkey1234567890"},
        )
        assert invalid_res.status_code == 401

        # 6. Revoke API key
        revoke_res = await client.delete(f"/api/keys/{key_id}")
        assert revoke_res.status_code == 200

        # 7. Verify revoked key cannot authenticate
        revoked_call = await client.post(
            "/api/route",
            json={"prompt": "Call after revoke"},
            headers={"X-API-Key": raw_key},
        )
        assert revoked_call.status_code == 401


@pytest.mark.asyncio
async def test_auth_required_flag():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Temporarily enable AUTH_REQUIRED
        orig_auth_req = settings.AUTH_REQUIRED
        try:
            settings.AUTH_REQUIRED = True
            
            # Unauthenticated call should fail with 401
            res = await client.post("/api/route", json={"prompt": "Hello world"})
            assert res.status_code == 401
            assert "Authentication required" in res.json()["detail"]
        finally:
            settings.AUTH_REQUIRED = orig_auth_req
