import hashlib
import secrets
import datetime
from typing import Optional, Tuple
from pydantic import BaseModel
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.storage.database import get_db
from app.storage.models import ApiKeyRecord, WorkspaceRecord
from app.config.settings import get_settings

settings = get_settings()


class AuthContext(BaseModel):
    workspace_id: str = "default"
    api_key_id: Optional[str] = None
    key_name: Optional[str] = None
    key_prefix: Optional[str] = None
    is_authenticated: bool = False
    rate_limit_rpm: int = 120
    rate_limit_tpm: int = 200000


def hash_api_key(key: str) -> str:
    """
    Computes a deterministic SHA-256 hash for secure storage and indexing.
    """
    return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()


def generate_api_key(prefix: str = "mr_live_") -> Tuple[str, str, str]:
    """
    Generates a cryptographically secure API key.
    Returns: (raw_key, key_hash, key_prefix)
    """
    random_secret = secrets.token_hex(24)
    raw_key = f"{prefix}{random_secret}"
    key_hash = hash_api_key(raw_key)
    key_prefix = f"{raw_key[:12]}..."
    return raw_key, key_hash, key_prefix


async def get_auth_context(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """
    FastAPI dependency for authenticating requests, validating API keys,
    and resolving tenant/workspace context.
    """
    raw_key = None
    if x_api_key:
        raw_key = x_api_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        raw_key = authorization[7:].strip()

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    if raw_key:
        key_hash = hash_api_key(raw_key)
        
        # Query ApiKeyRecord
        stmt = select(ApiKeyRecord).where(ApiKeyRecord.key_hash == key_hash)
        res = await db.execute(stmt)
        api_key = res.scalar_one_or_none()

        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key provided.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if not api_key.is_active:
            raise HTTPException(
                status_code=401,
                detail="API key has been revoked or deactivated.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if api_key.expires_at and api_key.expires_at < now_utc:
            raise HTTPException(
                status_code=401,
                detail="API key has expired.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Update last_used_at
        api_key.last_used_at = now_utc
        await db.commit()

        # Check Workspace
        ws_stmt = select(WorkspaceRecord).where(WorkspaceRecord.id == api_key.workspace_id)
        ws_res = await db.execute(ws_stmt)
        workspace = ws_res.scalar_one_or_none()

        if workspace and not workspace.is_active:
            raise HTTPException(
                status_code=403,
                detail="The workspace associated with this API key is disabled.",
            )

        rpm = api_key.rate_limit_rpm or (workspace.rate_limit_rpm if workspace else settings.DEFAULT_RATE_LIMIT_RPM)
        tpm = api_key.rate_limit_tpm or (workspace.rate_limit_tpm if workspace else settings.DEFAULT_RATE_LIMIT_TPM)

        return AuthContext(
            workspace_id=api_key.workspace_id,
            api_key_id=api_key.id,
            key_name=api_key.name,
            key_prefix=api_key.key_prefix,
            is_authenticated=True,
            rate_limit_rpm=rpm,
            rate_limit_tpm=tpm,
        )

    # If no key provided
    if settings.AUTH_REQUIRED:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid 'X-API-Key' header or 'Authorization: Bearer <key>'.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Development / Default mode (No auth required)
    target_workspace = x_workspace_id.strip() if x_workspace_id else "default"
    
    # Lookup workspace limits if exists
    ws_stmt = select(WorkspaceRecord).where(WorkspaceRecord.id == target_workspace)
    ws_res = await db.execute(ws_stmt)
    workspace = ws_res.scalar_one_or_none()
    
    rpm = workspace.rate_limit_rpm if workspace else settings.DEFAULT_RATE_LIMIT_RPM
    tpm = workspace.rate_limit_tpm if workspace else settings.DEFAULT_RATE_LIMIT_TPM

    return AuthContext(
        workspace_id=target_workspace,
        api_key_id=None,
        key_name="Unauthenticated Dev",
        key_prefix=None,
        is_authenticated=False,
        rate_limit_rpm=rpm,
        rate_limit_tpm=tpm,
    )
