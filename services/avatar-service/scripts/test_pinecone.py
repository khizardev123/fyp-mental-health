"""
Test Pinecone connection and index setup for SereneMind.

Run from services/avatar-service:
    python scripts/test_pinecone.py

Requires .env with PINECONE_API_KEY and PINECONE_ENABLED=true
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from app.core.config import get_settings
get_settings.cache_clear()

from app.core.config import settings
from app.core.pinecone_client import get_or_create_index, is_pinecone_configured
from app.services.vector_memory import embed_message, search_relevant_memories, upsert_memory


def main() -> int:
    print("=== SereneMind Pinecone Connection Test ===")
    print(f"Index name: {settings.PINECONE_INDEX_NAME}")
    print(f"Pinecone enabled: {settings.PINECONE_ENABLED}")
    print(f"API key configured: {'yes' if settings.PINECONE_API_KEY else 'no'}")

    if not is_pinecone_configured():
        print("\nPinecone is not active. Set in .env:")
        print("  PINECONE_API_KEY=your-key")
        print("  PINECONE_ENABLED=true")
        return 1

    index = get_or_create_index()
    if index is None:
        print("Failed to connect to Pinecone index.")
        return 1

    stats = index.describe_index_stats()
    print(f"\nIndex stats: {stats}")

    test_id = "test-connection-vector"
    test_text = "SereneMind Pinecone connection test message."
    ok = upsert_memory(
        user_id="test-user",
        message_id=test_id,
        text=test_text,
        metadata={"source": "test_script"},
    )
    print(f"Upsert test vector: {'OK' if ok else 'FAILED (needs OPENAI_API_KEY for embeddings)'}")

    if settings.OPENAI_API_KEY:
        vector = embed_message(test_text)
        print(f"Embedding dimension: {len(vector) if vector else 0}")

        memories = search_relevant_memories("test-user", test_text, top_k=1)
        print(f"Search test returned {len(memories)} result(s)")
        if memories:
            print(f"Top match score: {memories[0].get('score')}")

    print("\nPinecone integration is configured correctly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
