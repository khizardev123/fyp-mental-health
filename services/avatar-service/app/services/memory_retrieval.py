"""
Multi-strategy memory retrieval: factual, preference, and emotional memories.

Ranks by semantic similarity + recency. Never fabricates — only returns stored text.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Literal

from app.core.config import settings
from app.database.models import Message
from app.services.vector_memory import search_relevant_memories

logger = logging.getLogger(__name__)

MemoryType = Literal["factual", "preference", "emotional"]

RECALL_QUERY_PATTERNS = [
    r"what do you remember",
    r"what do you know about me",
    r"what have i told you",
    r"what did i tell you",
    r"do you remember me",
    r"tell me what you remember",
    r"what do you recall",
    r"summarize what you know",
    r"everything you know about me",
    r"(don'?t you|do you) remember",
    r"you forgot",
    r"what('?s| is) my name",
    r"what do you call me",
    r"what sport do i (like|enjoy|play|love)",
    r"what do i (like|love|enjoy)",
    r"what am i (building|working on|making)",
    r"what('?s| is) my (favourite|favorite)",
    r"who is my (favourite|favorite)",
    r"what('?s| is) my (degree|project|fyp|final year project)",
    r"what degree am i (studying|doing|taking|pursuing)",
    r"what (uni|university|college|major|course) am i",
    r"what did i say my name",
    r"do you know my name",
]

FACTUAL_PATTERNS = [
    r"\bmy name is\b",
    r"\bi am\b",
    r"\bi'm\b",
    r"\bcall me\b",
    r"\bname's\b",
    r"\byears old\b",
    r"\bi live in\b",
    r"\bi work as\b",
    r"\bi study\b",
    r"\bmy (degree|project|fyp|final year project) is\b",
    r"\bworking on my (fyp|project|final year project)\b",
]

PREFERENCE_PATTERNS = [
    r"\bfavourite\b",
    r"\bfavorite\b",
    r"\bi love\b",
    r"\bi like\b",
    r"\bhobby\b",
    r"\bhobbies\b",
    r"\bteam\b",
    r"\bplayer\b",
    r"\bsport\b",
    r"\bfootball\b",
    r"\bcricket\b",
    r"\bmusic\b",
    r"\bfan of\b",
]

EMOTIONAL_KEYWORDS = (
    "sad", "depressed", "anxious", "stress", "stressed", "worried", "overwhelmed",
    "lonely", "angry", "frustrated", "scared", "hurt", "upset", "hopeless",
    "failed", "fail", "exam", "exams", "grief", "panic", "nervous", "cry", "crying",
    "not happy", "unhappy", "miserable", "struggling", "pressure",
)

RECALL_EXPANDED_QUERY = (
    "user personal information name identity hobbies sports favorites teams players "
    "preferences likes loves emotional experiences exams stress"
)

CATEGORY_QUERIES: dict[MemoryType, str] = {
    "factual": "user name identity personal information who they are",
    "preference": "hobbies sports favorites favourite team player likes loves interests",
    "emotional": "feelings emotions stress anxiety sadness exams failure worry pressure",
}


def classify_memory_type(text: str) -> MemoryType:
    """Classify a user message for memory storage and retrieval."""
    lower = text.lower().strip()
    if not lower:
        return "factual"

    for pattern in FACTUAL_PATTERNS:
        if re.search(pattern, lower):
            return "factual"

    for pattern in PREFERENCE_PATTERNS:
        if re.search(pattern, lower):
            return "preference"

    if any(kw in lower for kw in EMOTIONAL_KEYWORDS):
        return "emotional"

    # Short declarative statements are usually factual/preferences
    if len(lower.split()) <= 12 and "?" not in lower:
        return "factual"

    return "emotional"


def is_memory_recall_query(message: str) -> bool:
    lower = message.strip().lower()
    return any(re.search(p, lower) for p in RECALL_QUERY_PATTERNS)


def _parse_timestamp(meta: dict[str, Any]) -> float:
    ts = meta.get("timestamp")
    if not ts:
        return 0.0
    try:
        if isinstance(ts, (int, float)):
            return float(ts)
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0


def _memory_key(mem: dict[str, Any]) -> str:
    text = (mem.get("text") or mem.get("metadata", {}).get("text", "")).strip().lower()
    return text[:100]


def _rank_score(
    mem: dict[str, Any],
    newest_ts: float,
    *,
    current_session_id: str | None = None,
) -> float:
    similarity = float(mem.get("score") or 0.5)
    ts = _parse_timestamp(mem.get("metadata") or {})
    if ts <= 0:
        recency = float(mem.get("recency_boost", 0.5))
    elif newest_ts > 0:
        recency = ts / newest_ts
    else:
        recency = 0.5
    session_boost = 0.0
    if current_session_id:
        mem_session = (mem.get("metadata") or {}).get("session_id")
        if mem_session == current_session_id:
            session_boost = 0.04
    return similarity * 0.62 + recency * 0.34 + session_boost


def _message_to_memory(msg: Message, *, recency_index: int, total: int) -> dict[str, Any]:
    text = (msg.content or "").strip()
    memory_type = classify_memory_type(text)
    recency_boost = (recency_index + 1) / max(total, 1)
    ts = msg.timestamp.isoformat() if msg.timestamp else ""
    return {
        "id": f"session-{msg.id}",
        "score": 0.95,
        "text": text,
        "metadata": {
            "source": "session_db",
            "session_id": msg.session_id,
            "memory_type": memory_type,
            "emotion": msg.emotion,
            "timestamp": ts,
        },
        "memory_type": memory_type,
        "recency_boost": recency_boost,
    }


def session_user_memories(messages: list[Message], *, limit: int | None = None) -> list[dict[str, Any]]:
    """All user turns in session — ground truth for same-conversation recall."""
    limit = limit or settings.RAG_SESSION_MEMORY_LIMIT
    user_msgs = [m for m in messages if m.role == "user"]
    if limit and len(user_msgs) > limit:
        user_msgs = user_msgs[-limit:]
    total = len(user_msgs)
    return [
        _message_to_memory(msg, recency_index=i, total=total)
        for i, msg in enumerate(user_msgs)
    ]


def _merge_memories(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for group in groups:
        for mem in group:
            key = _memory_key(mem)
            if not key:
                continue
            existing = merged.get(key)
            if existing is None or (mem.get("score") or 0) > (existing.get("score") or 0):
                merged[key] = mem
            elif existing is not None:
                # Keep higher recency boost
                if (mem.get("recency_boost") or 0) > (existing.get("recency_boost") or 0):
                    existing["recency_boost"] = mem["recency_boost"]
    return list(merged.values())


def retrieve_memories_for_prompt(
    *,
    user_id: str,
    query: str,
    session_id: str,
    session_user_messages: list[Message],
    timings: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve factual, preference, and emotional memories; rank by similarity + recency.
    """
    t0 = time.perf_counter()
    is_recall = is_memory_recall_query(query)
    retrieve_k = settings.RAG_RETRIEVE_K
    threshold = settings.RAG_SIMILARITY_THRESHOLD
    if is_recall:
        threshold = settings.RAG_RECALL_THRESHOLD

    groups: list[list[dict[str, Any]]] = []

    # Primary semantic search on user message
    groups.append(
        search_relevant_memories(
            user_id,
            query,
            top_k=retrieve_k,
            timings=timings,
            session_id=session_id,
            threshold=threshold,
        )
    )

    search_query = RECALL_EXPANDED_QUERY if is_recall else query

    # Category-targeted searches (broader recall for facts/preferences)
    for memory_type, cat_query in CATEGORY_QUERIES.items():
        cat_threshold = {
            "factual": settings.RAG_FACTUAL_THRESHOLD,
            "preference": settings.RAG_PREFERENCE_THRESHOLD,
            "emotional": settings.RAG_EMOTIONAL_THRESHOLD,
        }[memory_type]
        if is_recall:
            cat_threshold = min(cat_threshold, settings.RAG_RECALL_THRESHOLD)

        hits = search_relevant_memories(
            user_id,
            f"{search_query} {cat_query}",
            top_k=settings.RAG_CATEGORY_TOP_K,
            session_id=session_id,
            threshold=cat_threshold,
        )
        for hit in hits:
            meta = hit.setdefault("metadata", {})
            meta.setdefault("memory_type", memory_type)
            hit["memory_type"] = meta.get("memory_type", memory_type)
        groups.append(hits)

    # Session DB — full user history (not limited by chat HISTORY_WINDOW)
    db_limit = settings.RAG_SESSION_MEMORY_LIMIT if is_recall else min(12, settings.RAG_SESSION_MEMORY_LIMIT)
    session_mems = session_user_memories(session_user_messages, limit=db_limit)
    groups.append(session_mems)

    merged = _merge_memories(*groups)

    # Exclude current message if already in prior (shouldn't be) — handled by caller timing

    newest_ts = max((_parse_timestamp(m.get("metadata") or {}) for m in merged), default=1.0) or 1.0
    for mem in merged:
        meta = mem.get("metadata") or {}
        if "memory_type" not in meta and "memory_type" not in mem:
            mem_type = classify_memory_type(mem.get("text", ""))
            meta["memory_type"] = mem_type
            mem["memory_type"] = mem_type
        mem["rank_score"] = _rank_score(mem, newest_ts, current_session_id=session_id)

    merged.sort(key=lambda m: m.get("rank_score", 0), reverse=True)

    # On recall queries, include every session user turn (ground truth for "what do you remember")
    if is_recall and session_mems:
        selected: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for mem in session_mems:
            key = _memory_key(mem)
            if key and key not in seen_keys:
                selected.append(mem)
                seen_keys.add(key)
        for mem in merged:
            key = _memory_key(mem)
            if key and key not in seen_keys:
                selected.append(mem)
                seen_keys.add(key)
        cap = max(settings.RAG_TOP_K, len(session_mems))
        result = selected[:cap]
    else:
        result = merged[: settings.RAG_TOP_K]

    elapsed = (time.perf_counter() - t0) * 1000
    if timings is not None:
        timings["memory_retrieval_ms"] = elapsed

    type_counts: dict[str, int] = {}
    for mem in result:
        mt = mem.get("memory_type") or mem.get("metadata", {}).get("memory_type", "unknown")
        type_counts[mt] = type_counts.get(mt, 0) + 1

    logger.info(
        "[RAG] retrieve_memories | recall=%s | total=%d | factual=%d pref=%d emotional=%d",
        is_recall,
        len(result),
        type_counts.get("factual", 0),
        type_counts.get("preference", 0),
        type_counts.get("emotional", 0),
    )
    for i, mem in enumerate(result):
        logger.info(
            "[RAG]   [%d] type=%s rank=%.3f | %r",
            i,
            mem.get("memory_type", "?"),
            mem.get("rank_score", 0),
            (mem.get("text") or "")[:90],
        )

    return result
