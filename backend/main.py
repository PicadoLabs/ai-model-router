import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.config.settings import get_settings
from app.storage.database import init_db, AsyncSessionLocal
from app.storage.models import RequestRecord
from app.api.routes import router as api_router
from sqlalchemy import select, desc

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and seed defaults
    await init_db()
    yield


app = FastAPI(
    title="Model Router",
    description="Intelligent LLM Request Routing Platform — AI Traffic Control Room",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/traffic/stream")
async def stream_live_traffic():
    """
    SSE Live Stream endpoint for the Traffic Control Room visualization.
    Pushes newly persisted requests to connected frontend clients.
    """
    async def event_generator():
        last_seen_id = None
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    res = await session.execute(
                        select(RequestRecord).order_by(desc(RequestRecord.timestamp)).limit(1)
                    )
                    latest = res.scalar_one_or_none()
                    if latest and latest.request_id != last_seen_id:
                        last_seen_id = latest.request_id
                        payload = {
                            "request_id": latest.request_id,
                            "timestamp": latest.timestamp.isoformat() if latest.timestamp else "",
                            "prompt": latest.prompt,
                            "task_type": latest.task_type,
                            "complexity": latest.complexity,
                            "selected_model": latest.selected_model,
                            "provider": latest.provider,
                            "status": latest.status,
                            "total_latency_ms": latest.total_latency_ms,
                            "estimated_cost": latest.estimated_cost,
                        }
                        yield {
                            "event": "traffic_event",
                            "data": json.dumps(payload),
                        }
            except Exception:
                pass
            await asyncio.sleep(1.5)

    return EventSourceResponse(event_generator())


@app.get("/")
async def root():
    return {
        "message": "Model Router AI Control Room Backend is active.",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
