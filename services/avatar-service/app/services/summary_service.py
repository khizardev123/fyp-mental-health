"""Session and user summary generation with in-memory cache."""

import logging
import os

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Message, Session as ChatSession, UserSummary

logger = logging.getLogger(__name__)

_openai_key = os.getenv("OPENAI_API_KEY")
_openai_client = None
if _openai_key:
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=_openai_key)
    except ImportError:
        pass

# In-memory cache for active sessions (cleared on process restart)
_user_summary_cache: dict[str, str] = {}
_session_summary_cache: dict[str, str] = {}


def invalidate_summary_cache(*, user_id: str | None = None, session_id: str | None = None) -> None:
    if user_id and user_id in _user_summary_cache:
        del _user_summary_cache[user_id]
    if session_id and session_id in _session_summary_cache:
        del _session_summary_cache[session_id]


def get_user_summary_text(db: Session, user_id: str) -> str | None:
    if user_id in _user_summary_cache:
        return _user_summary_cache[user_id]

    row = (
        db.query(UserSummary)
        .filter(UserSummary.user_id == user_id)
        .order_by(UserSummary.updated_at.desc())
        .first()
    )
    text = row.summary_text if row else None
    if text:
        _user_summary_cache[user_id] = text
    return text


def get_session_summary_text(session: ChatSession) -> str | None:
    if session.id in _session_summary_cache:
        return _session_summary_cache[session.id]

    text = session.summary
    if text:
        _session_summary_cache[session.id] = text
    return text


def count_session_messages(db: Session, session_id: str) -> int:
    return db.query(Message).filter(Message.session_id == session_id).count()


def _generate_summary_text(messages: list[Message]) -> str:
    lines = []
    for msg in messages[-40:]:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")

    transcript = "\n".join(lines)
    if _openai_client:
        try:
            response = _openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Summarize this mental health chat session in 3-5 sentences. "
                            "Focus on emotional themes, concerns, and supportive context. "
                            "Do not include crisis instructions."
                        ),
                    },
                    {"role": "user", "content": transcript},
                ],
                max_tokens=180,
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning("LLM summary failed: %s", exc)

    user_msgs = [m.content for m in messages if m.role == "user"][-5:]
    return "Recent themes: " + "; ".join(user_msgs[:3]) if user_msgs else "No significant themes yet."


def maybe_update_summaries(db: Session, session: ChatSession, user_id: str) -> None:
    """After every N messages, generate session summary and merge into user long-term memory."""
    total = count_session_messages(db, session.id)
    if total == 0 or total % settings.SESSION_SUMMARY_INTERVAL != 0:
        return

    all_messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    summary = _generate_summary_text(all_messages)
    session.summary = summary
    _session_summary_cache[session.id] = summary
    db.commit()

    existing = (
        db.query(UserSummary)
        .filter(UserSummary.user_id == user_id)
        .order_by(UserSummary.updated_at.desc())
        .first()
    )

    if existing:
        merged = f"{existing.summary_text}\n\n[Updated session]: {summary}".strip()
        if len(merged) > 4000:
            merged = merged[-4000:]
        existing.summary_text = merged
        _user_summary_cache[user_id] = merged
    else:
        db.add(UserSummary(user_id=user_id, summary_text=summary))
        _user_summary_cache[user_id] = summary

    db.commit()
    logger.info("Updated summaries for user %s after %d messages", user_id, total)
