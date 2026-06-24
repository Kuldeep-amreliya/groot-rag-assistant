"""
memory_cache.py
===============
Redis-backed short-term conversation cache. Falls back to Postgres
transparently if Redis is unavailable — Redis is a latency optimization,
never a single point of failure for chat to keep working.

Usage:
  - After storing a message in Postgres, call push_message(...) to also cache it.
  - When reading short-term context, call get_recent_messages(...) first;
    if it returns None (Redis down or cache miss), fall back to Postgres.
  - On conversation delete, call invalidate(...) to clear the cache.

Dependencies: pip install redis
"""

import json
import logging
import os
from typing import List, Optional

import redis

logger = logging.getLogger("rag_backend")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SHORT_TERM_WINDOW = 6  # keep in sync with backend.Config.SHORT_TERM_WINDOW
REDIS_TTL_SECONDS = 6 * 60 * 60  # 6h idle TTL; conversation is durable in Postgres regardless

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Lazily connect; return None (not raise) if Redis is unreachable so
    callers can fall back to Postgres without crashing the chat flow."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        client = redis.Redis.from_url(
            REDIS_URL, socket_connect_timeout=2, decode_responses=True
        )
        client.ping()
        _redis_client = client
        logger.info("Redis connected: %s", REDIS_URL)
        return _redis_client
    except Exception as e:
        logger.warning(
            "Redis unavailable, falling back to Postgres-only memory: %s", e
        )
        return None


def _key(conversation_id: str) -> str:
    """Redis key for a conversation's short-term message cache."""
    return f"chat:history:{conversation_id}"


def push_message(conversation_id: str, role: str, content: str) -> None:
    """Append a message to the Redis short-term window. Best-effort only —
    Postgres write (db.add_message) is the source of truth and must happen
    separately/regardless of this call's success.

    Call this after every db.add_message(...) in the same transaction.
    """
    client = get_redis()
    if client is None:
        return
    try:
        key = _key(conversation_id)
        entry = json.dumps({"role": role, "content": content})
        client.rpush(key, entry)
        client.ltrim(key, -SHORT_TERM_WINDOW, -1)
        client.expire(key, REDIS_TTL_SECONDS)
    except Exception as e:
        logger.warning(
            "Redis push_message failed for %s (non-fatal, continuing): %s",
            conversation_id,
            e,
        )


def get_recent_messages(conversation_id: str) -> Optional[List[dict]]:
    """Return cached recent messages as dicts with 'role'/'content' keys, or None
    if Redis is unavailable or the key is missing (cache miss) so the caller
    knows to fall back to Postgres.

    Returns: List[{"role": str, "content": str}] or None
    """
    client = get_redis()
    if client is None:
        return None
    try:
        key = _key(conversation_id)
        raw = client.lrange(key, 0, -1)
        if not raw:
            return None
        return [json.loads(r) for r in raw]
    except Exception as e:
        logger.warning(
            "Redis get_recent_messages failed for %s (falling back to Postgres): %s",
            conversation_id,
            e,
        )
        return None


def invalidate(conversation_id: str) -> None:
    """Clear the cached message list for a conversation (e.g., on deletion)."""
    client = get_redis()
    if client is None:
        return
    try:
        client.delete(_key(conversation_id))
    except Exception as e:
        logger.warning(
            "Redis invalidate failed for %s (non-fatal): %s", conversation_id, e
        )