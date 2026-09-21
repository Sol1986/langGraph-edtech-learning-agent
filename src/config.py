"""Centralized environment configuration.
"""

import os

from dotenv import load_dotenv

load_dotenv()

QDRANT_URL: str | None = os.getenv("QDRANT_URL")
QDRANT_API_KEY: str | None = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = "pdf_documents"

# 3. Grab the connection string securely from the environment
REDIS_URL: str | None = os.getenv("REDIS_URL")


def require_qdrant_config() -> tuple[str, str]:
    """Raise a clear error early rather than letting Qdrant client calls fail cryptically."""
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must be set (.env).")
    return QDRANT_URL, QDRANT_API_KEY

def require_redis_url() -> str:
    """Raise a clear error early rather than letting the Redis client fail cryptically."""
    if not REDIS_URL:
        raise RuntimeError("REDIS_URL must be set (.env).")
    return REDIS_URL