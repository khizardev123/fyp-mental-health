"""
End-to-end backend flow test: Auth → Chat → ML → Pinecone → RAG → Response

Run from services/avatar-service (AI service must be on :8000):
    python scripts/test_full_flow.py
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from app.core.config import get_settings
get_settings.cache_clear()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

from sqlalchemy.orm import Session

from app.auth.password import hash_password
from app.chat_service import process_chat_message
from app.core.config import settings
from app.core.pinecone_client import is_pinecone_configured
from app.database.models import User
from app.database.session import SessionLocal, init_db


async def run_flow() -> int:
    print("=" * 60)
    print("SereneMind Full Flow Test")
    print("=" * 60)
    print(f"OpenAI:   {settings.openai_active}")
    print(f"Ollama:   {settings.OLLAMA_MODEL} (fallback: {settings.OLLAMA_FALLBACK_MODEL})")
    print(f"Pinecone: {is_pinecone_configured()}")
    print(f"AI URL:   {settings.AI_SERVICE_URL}")

    init_db()
    db: Session = SessionLocal()

    try:
        email = "flowtest@example.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name="Flow Test", email=email, password_hash=hash_password("test12345"))
            db.add(user)
            db.commit()
            db.refresh(user)
        print(f"\n[AUTH] User: {user.id} ({user.email})")

        session_id = None
        messages = [
            "Hi",
            "I feel really stressed about my exams next week.",
            "Last time I failed an exam I couldn't sleep for days.",
            "My exams are coming up again and I'm panicking.",
        ]

        for i, msg in enumerate(messages, 1):
            print(f"\n--- Chat turn {i}: {msg!r} ---")
            result = await process_chat_message(
                db,
                user=user,
                session_id=session_id,
                message=msg,
            )
            session_id = result["session_id"]
            print(f"[CHAT] reply: {result['reply'][:120]}...")
            print(f"[ML]   emotion={result['emotion']} | crisis={result['crisis']} | mental_state={result['mental_state']}")
            print(f"[RAG]  memories_used={result['memories_used']} | source={result['source']}")

        print("\n" + "=" * 60)
        print("Full flow completed successfully")
        print(f"Session ID: {session_id}")
        print("=" * 60)
        return 0
    except Exception as exc:
        print(f"\nFLOW FAILED: {exc}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_flow()))
