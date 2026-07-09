"""Pinecone client initialization — API key loaded from environment only."""

import logging
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_pinecone_client: Any = None
_index: Any = None


def is_pinecone_configured() -> bool:
    return settings.pinecone_active


def get_pinecone_client():
    global _pinecone_client
    if not is_pinecone_configured():
        return None
    if _pinecone_client is None:
        from pinecone import Pinecone

        _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
        logger.info("Pinecone client initialized")
    return _pinecone_client


def get_or_create_index():
    """Return Pinecone index, creating it if it does not exist."""
    global _index
    if not is_pinecone_configured():
        return None

    if _index is not None:
        return _index

    pc = get_pinecone_client()
    if pc is None:
        return None

    index_name = settings.PINECONE_INDEX_NAME
    existing = {idx.name for idx in pc.list_indexes()}

    if index_name not in existing:
        from pinecone import ServerlessSpec
        import time

        logger.info("Creating Pinecone index: %s", index_name)
        pc.create_index(
            name=index_name,
            dimension=settings.PINECONE_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
        )
        logger.info("Waiting for new index to become ready...")
        time.sleep(15)

    _index = pc.Index(index_name)
    logger.info("Connected to Pinecone index: %s", index_name)
    return _index
