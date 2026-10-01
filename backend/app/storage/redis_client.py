import json
import logging
from typing import Optional
import redis.asyncio as aioredis
from app.config.settings import get_settings

logger = logging.getLogger("model_router.redis")
settings = get_settings()

_redis_client: Optional[aioredis.Redis] = None

async def init_redis():
    global _redis_client
    if settings.REDIS_URL:
        try:
            _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await _redis_client.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            _redis_client = None
    else:
        logger.info("REDIS_URL not set. Running without Redis Pub/Sub.")

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()

def get_redis() -> Optional[aioredis.Redis]:
    return _redis_client

async def publish_traffic_event(event_data: dict):
    if _redis_client:
        try:
            await _redis_client.publish("traffic_stream", json.dumps(event_data))
        except Exception as e:
            logger.error(f"Failed to publish traffic event: {e}")
