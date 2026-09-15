"""Centralized environment configuration.

Loaded once at import time so every module (quiz_agent, pdf_ingest, server)
reads identical values regardless of import order. This is the single fix
for the `load_dotenv` (missing call) bug present in the original scripts.
"""

import os

from dotenv import load_dotenv

load_dotenv()

QDRANT_URL: str | None = os.getenv("QDRANT_URL")
QDRANT_API_KEY: str | None = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = "pdf_documents"


def require_qdrant_config() -> tuple[str, str]:
    """Raise a clear error early rather than letting Qdrant client calls fail cryptically."""
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must be set (.env).")
    return QDRANT_URL, QDRANT_API_KEY
