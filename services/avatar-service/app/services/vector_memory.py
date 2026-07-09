"""
Vector memory layer for SereneMind (Pinecone).

Stores embedded user messages for semantic retrieval (RAG).
Supports OpenAI embeddings with Pinecone Inference fallback.
"""

import logging
import time
from typing import Any

from app.core.config import settings
from app.core.pinecone_client import get_or_create_index, get_pinecone_client, is_pinecone_configured

logger = logging.getLogger(__name__)


def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        elif isinstance(value, list):
            clean[key] = [str(v) for v in value]
        else:
            clean[key] = str(value)
    return clean


def _embed_with_openai(text: str) -> list[float] | None:
    if not settings.openai_active:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text[:8000],
        )
        return response.data[0].embedding
    except Exception as exc:
        err = str(exc).lower()
        if "quota" in err or "429" in err or "insufficient" in err:
            logger.warning("[RAG] OpenAI embedding quota exceeded — trying Pinecone Inference")
        else:
            logger.error("[RAG] OpenAI embed failed: %s", exc)
        return None


def _embed_with_pinecone(text: str) -> list[float] | None:
    pc = get_pinecone_client()
    if pc is None:
        return None
    try:
        result = pc.inference.embed(
            model=settings.PINECONE_EMBED_MODEL,
            inputs=[text[:8000]],
            parameters={"input_type": "passage", "truncate": "END"},
        )
        vector = result.data[0].values
        logger.info(
            "[RAG] Pinecone Inference embedding | model=%s | dim=%d",
            settings.PINECONE_EMBED_MODEL,
            len(vector),
        )
        return vector
    except Exception as exc:
        logger.error("[RAG] Pinecone Inference embed failed: %s", exc, exc_info=True)
        return None


def embed_message(text: str) -> list[float] | None:
    """Generate embedding via configured provider with automatic fallback."""
    provider = settings.EMBEDDING_PROVIDER.lower()
    vector = None

    if provider in ("auto", "openai"):
        vector = _embed_with_openai(text)
    if vector is None and provider in ("auto", "pinecone"):
        vector = _embed_with_pinecone(text)

    if vector:
        logger.info("[RAG] Embedding created | dim=%d | chars=%d", len(vector), len(text))
    else:
        logger.warning("[RAG] embed_message failed — no provider available")
    return vector


def upsert_memory(
    *,
    user_id: str,
    message_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    if not is_pinecone_configured():
        logger.debug("[RAG] upsert_memory skipped — Pinecone not active")
        return False

    vector = embed_message(text)
    if vector is None:
        logger.warning("[RAG] upsert_memory aborted — no embedding for message_id=%s", message_id)
        return False

    index = get_or_create_index()
    if index is None:
        logger.error("[RAG] upsert_memory aborted — index unavailable")
        return False

    meta = _sanitize_metadata({"user_id": user_id, "text": text[:500], **(metadata or {})})
    try:
        index.upsert(vectors=[{"id": message_id, "values": vector, "metadata": meta}])
        logger.info(
            "[RAG] Pinecone upsert SUCCESS | id=%s | user=%s | preview=%r",
            message_id,
            user_id,
            text[:80],
        )
        return True
    except Exception as exc:
        logger.error("[RAG] Pinecone upsert FAILED | id=%s | error=%s", message_id, exc, exc_info=True)
        return False


def search_relevant_memories(
    user_id: str,
    query: str,
    top_k: int | None = None,
    timings: dict[str, float] | None = None,
    session_id: str | None = None,
    threshold: float | None = None,
) -> list[dict[str, Any]]:
    if not is_pinecone_configured():
        logger.debug("[RAG] search skipped — Pinecone not active")
        return []

    t_embed = time.perf_counter()
    vector = embed_message(query)
    if timings is not None:
        timings["pinecone_embed_ms"] = (time.perf_counter() - t_embed) * 1000

    if vector is None:
        logger.warning("[RAG] search aborted — no query embedding")
        return []

    index = get_or_create_index()
    if index is None:
        logger.error("[RAG] search aborted — index unavailable")
        return []

    k = top_k or settings.RAG_TOP_K
    try:
        t_query = time.perf_counter()
        pine_filter: dict[str, Any] = {"user_id": {"$eq": user_id}}
        if session_id:
            pine_filter = {
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"session_id": {"$eq": session_id}},
                ]
            }
        results = index.query(
            vector=vector,
            top_k=k,
            include_metadata=True,
            filter=pine_filter,
        )
        matches = results.get("matches") or []
        if session_id and not matches:
            results = index.query(
                vector=vector,
                top_k=k,
                include_metadata=True,
                filter={"user_id": {"$eq": user_id}},
            )
            matches = results.get("matches") or []
        if timings is not None:
            timings["pinecone_query_ms"] = (time.perf_counter() - t_query) * 1000

        t_filter = time.perf_counter()
        sim_threshold = threshold if threshold is not None else settings.RAG_SIMILARITY_THRESHOLD
        memories = []
        for match in matches:
            score = match.get("score") or 0
            if score < sim_threshold:
                logger.debug(
                    "[RAG] Skipping low-similarity memory score=%.4f < %.2f",
                    score,
                    sim_threshold,
                )
                continue
            meta = match.get("metadata") or {}
            memories.append({
                "id": match.get("id"),
                "score": score,
                "text": meta.get("text", ""),
                "metadata": meta,
                "memory_type": meta.get("memory_type"),
            })

        if timings is not None:
            timings["memory_filtering_ms"] = (time.perf_counter() - t_filter) * 1000

        logger.info(
            "[RAG] Retrieved %d memories (threshold>=%.2f) for user=%s | query=%r",
            len(memories),
            sim_threshold,
            user_id,
            query[:80],
        )
        for i, mem in enumerate(memories):
            logger.info(
                "[RAG]   memory[%d] score=%.4f | %r",
                i,
                mem.get("score") or 0,
                (mem.get("text") or "")[:100],
            )
        return memories
    except Exception as exc:
        logger.error("[RAG] search_relevant_memories failed: %s", exc, exc_info=True)
        return []
