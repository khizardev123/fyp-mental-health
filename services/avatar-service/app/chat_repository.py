from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Message, Session as ChatSession, User


def get_or_create_user(db: Session, user_id: str | None, name: str | None = None, email: str | None = None) -> User:
    if user_id:
        user = db.get(User, user_id)
        if user:
            return user
        user = User(
            id=user_id,
            name=name or "Guest",
            email=email or f"guest-{user_id}@example.com",
        )
    else:
        user = User(
            name=name or "Guest",
            email=email or "guest-anonymous@example.com",
        )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_session(db: Session, user: User, session_id: str | None) -> ChatSession:
    """Reuse an open session, or create a new one.

    Ended sessions are never reopened — a new Session row is created so
    emotional summaries stay scoped to logical session boundaries (Phase F-4).
    """
    if session_id:
        session = db.get(ChatSession, session_id)
        if session and session.user_id == user.id and session.ended_at is None:
            return session

    session = ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_session(db: Session, user: User) -> ChatSession:
    """Explicitly start a new logical session (does not clear prior sessions)."""
    session = ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_recent_messages(db: Session, session_id: str, limit: int | None = None) -> list[Message]:
    limit = limit or settings.HISTORY_WINDOW
    return (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
        .all()[::-1]
    )


def get_session_user_messages(db: Session, session_id: str, limit: int | None = None) -> list[Message]:
    """All user messages in a session — used for memory recall (not chat history window)."""
    limit = limit or settings.RAG_SESSION_MEMORY_LIMIT
    q = (
        db.query(Message)
        .filter(Message.session_id == session_id, Message.role == "user")
        .order_by(Message.timestamp.asc())
    )
    if limit:
        q = q.limit(limit)
    return q.all()


def messages_to_history(messages: list[Message]) -> list[dict[str, str]]:
    history = []
    for msg in messages:
        role = "assistant" if msg.role in ("assistant", "avatar") else "user"
        history.append({"role": role, "content": msg.content})
    return history


def session_context_memories(messages: list[Message], *, limit: int = 3) -> list[dict[str, Any]]:
    """Recent user turns from DB — reliable fallback when Pinecone is empty or racing."""
    user_msgs = [m for m in messages if m.role == "user"]
    recent = user_msgs[-limit:] if len(user_msgs) > limit else user_msgs
    memories: list[dict[str, Any]] = []
    for msg in recent:
        text = (msg.content or "").strip()
        if not text:
            continue
        memories.append({
            "id": f"session-{msg.id}",
            "score": 1.0,
            "text": text,
            "metadata": {
                "source": "session_db",
                "session_id": msg.session_id,
                "emotion": msg.emotion,
            },
        })
    return memories


def analysis_from_stored_message(msg: Message) -> dict[str, Any]:
    """Re-finalize analysis from message text so dashboard fields stay consistent."""
    from app.emotion_pipeline import finalize_emotion_analysis

    stub = {
        "ml_raw_label": "normal",
        "raw_label": "normal",
        "emotion": "neutral",
        "mental_state": "Stable",
        "confidence": float(msg.emotion_confidence or 0.5),
        "all_scores": {"normal": 0.5},
        "crisis_risk": msg.crisis_level or "LOW",
        "crisis_probability": float(msg.crisis_score or 0.0),
        "requires_immediate_action": (msg.crisis_level or "LOW") in ("HIGH", "CRISIS"),
        "severity_rating": 2,
        "tags": [],
        "semantic_summary": "",
        "triggered_by": msg.intent or "stored",
        "processing_time_ms": 0.0,
        "model_version": "4.0.0",
    }
    result = finalize_emotion_analysis(msg.content, stub)
    if msg.crisis_level in ("HIGH", "CRISIS"):
        result["crisis_risk"] = msg.crisis_level
        result["requires_immediate_action"] = True
    return result


def save_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    *,
    emotion: str | None = None,
    emotion_confidence: float | None = None,
    mental_state: str | None = None,
    mh_confidence: float | None = None,
    crisis_score: float | None = None,
    crisis_level: str | None = None,
    intent: str | None = None,
) -> Message:
    message = Message(
        session_id=session_id,
        role=role,
        content=content,
        emotion=emotion,
        emotion_confidence=emotion_confidence,
        mental_state=mental_state,
        mh_confidence=mh_confidence,
        crisis_score=crisis_score,
        crisis_level=crisis_level,
        intent=intent,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def rolling_avatar_emotion(db: Session, session_id: str, window: int | None = None) -> str:
    from collections import Counter

    window = window or settings.AVATAR_EMOTION_WINDOW
    recent_user = (
        db.query(Message)
        .filter(Message.session_id == session_id, Message.role == "user", Message.emotion.isnot(None))
        .order_by(Message.timestamp.desc())
        .limit(window)
        .all()
    )
    if not recent_user:
        return "neutral"

    emotions = [m.emotion for m in recent_user if m.emotion]
    if not emotions:
        return "neutral"

    counts = Counter(emotions)
    return counts.most_common(1)[0][0]


def build_analysis_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Extract ML primitives only — dashboard fields come from finalize_emotion_analysis."""
    unified = data.get("unified") or {}
    raw_label = unified.get("raw_label", "normal")
    return {
        "ml_raw_label": raw_label,
        "ml_confidence": unified.get("confidence") or data.get("emotion", {}).get("confidence", 0.0),
        "confidence": unified.get("confidence") or data.get("emotion", {}).get("confidence", 0.0),
        "all_scores": unified.get("all_scores") or data.get("emotion", {}).get("all_emotions", {}),
        "crisis_risk": unified.get("crisis_risk") or data.get("crisis", {}).get("risk_level", "LOW"),
        "crisis_probability": unified.get("crisis_probability") or data.get("crisis", {}).get("crisis_probability", 0.0),
        "requires_immediate_action": unified.get("requires_immediate_action")
        or data.get("crisis", {}).get("requires_immediate_action", False),
        "processing_time_ms": data.get("processing_time_ms", 0.0),
        "model_version": data.get("model_version", "4.0.0"),
        "triggered_by": unified.get("triggered_by", "model"),
    }
