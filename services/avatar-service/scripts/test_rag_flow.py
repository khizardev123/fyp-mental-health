"""
Full Pinecone + RAG integration test for SereneMind.

Run from services/avatar-service:
    python scripts/test_pinecone.py
    python scripts/test_rag_flow.py
"""

import logging
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from app.core.config import get_settings
get_settings.cache_clear()

from app.core.config import settings
from app.core.pinecone_client import get_or_create_index, is_pinecone_configured
from app.services.vector_memory import embed_message, search_relevant_memories, upsert_memory


def _status(label: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def test_embeddings() -> bool:
    print("\n--- 1. Embeddings ---")
    if not settings.openai_active:
        return _status("OpenAI API key", False, "Set OPENAI_API_KEY in .env")
    vector = embed_message("I feel anxious before exams.")
    return _status("Embedding generation", vector is not None and len(vector) == settings.PINECONE_DIMENSION,
                   f"dim={len(vector) if vector else 0}")


def test_connection() -> bool:
    print("\n--- 2. Pinecone Connection ---")
    if not is_pinecone_configured():
        return _status("Pinecone configured", False, "Set PINECONE_API_KEY in .env")
    index = get_or_create_index()
    if index is None:
        return _status("Index connection", False)
    stats = index.describe_index_stats()
    print(f"       Index stats: {stats}")
    return _status("Index connection", True, settings.PINECONE_INDEX_NAME)


def test_upsert(user_id: str) -> bool:
    print("\n--- 3. Memory Upsert ---")
    msg_id = f"test-{uuid.uuid4().hex[:8]}"
    text = "I always panic before exams and feel overwhelmed with stress."
    ok = upsert_memory(user_id=user_id, message_id=msg_id, text=text, metadata={"source": "rag_test"})
    return _status("Upsert memory", ok, msg_id)


def test_retrieval(user_id: str) -> bool:
    print("\n--- 4. Semantic Retrieval ---")
    import time
    time.sleep(2)  # allow index to settle after upsert
    memories = search_relevant_memories(user_id, "My exams are next week and I'm worried", top_k=3)
    ok = len(memories) > 0
    for m in memories:
        print(f"       score={m.get('score', 0):.4f} | {m.get('text', '')[:80]}")
    return _status("Semantic search", ok, f"{len(memories)} results")


def test_rag_conversation(user_id: str) -> bool:
    print("\n--- 5. RAG Conversation Simulation ---")
    emotional_messages = [
        "I had a terrible day today.",
        "My exam went badly and I feel like a failure.",
        "I've been stressed about university deadlines all week.",
    ]
    ids = []
    for msg in emotional_messages:
        mid = f"rag-{uuid.uuid4().hex[:8]}"
        ok = upsert_memory(user_id=user_id, message_id=mid, text=msg, metadata={"source": "rag_convo_test"})
        ids.append(mid)
        _status(f"Store: {msg[:40]}...", ok)

    import time
    time.sleep(3)

    follow_up = "My exams are next week and I'm feeling anxious again"
    memories = search_relevant_memories(user_id, follow_up, top_k=3)
    print(f"\n  Follow-up query: {follow_up!r}")
    relevant = [m for m in memories if any(kw in (m.get("text") or "").lower() for kw in ("exam", "stress", "anxious", "deadline"))]
    for m in memories:
        print(f"       score={m.get('score', 0):.4f} | {m.get('text', '')[:90]}")

    return _status("Follow-up retrieves exam/stress memories", len(memories) > 0,
                   f"{len(memories)} total, {len(relevant)} exam/stress related")


def main() -> int:
    print("=" * 60)
    print("SereneMind Pinecone + RAG Integration Test")
    print("=" * 60)
    print(f"OpenAI active:    {settings.openai_active}")
    print(f"Pinecone active:  {is_pinecone_configured()}")
    print(f"Index:            {settings.PINECONE_INDEX_NAME}")

    user_id = f"rag-test-{uuid.uuid4().hex[:6]}"
    print(f"Test user_id:     {user_id}")

    results = [
        test_embeddings(),
        test_connection(),
        test_upsert(user_id),
        test_retrieval(user_id),
        test_rag_conversation(user_id),
    ]

    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
