"""Session emotion summary — reuses stored message emotions (no new ML model)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.database.models import Message, Session as ChatSession
from app.services.summary_service import invalidate_summary_cache

_FRIENDLY = {
    "joy": "happy",
    "happy": "happy",
    "joyful": "happy",
    "love": "warm",
    "surprise": "surprised",
    "sadness": "sad",
    "sad": "sad",
    "grief": "grief",
    "anger": "angry",
    "angry": "angry",
    "fear": "fearful",
    "anxiety": "anxious",
    "anxious": "anxious",
    "stress": "stressed",
    "stressed": "stressed",
    "calm": "calm",
    "neutral": "calm",
    "normal": "calm",
    "stable": "calm",
    "hopeful": "hopeful",
    "hope": "hopeful",
}

_RECOMMENDATIONS = {
    "anxious": (
        "Continue journaling and remember that emotional changes are normal. "
        "Take short breaks, breathe slowly, and reach out for support whenever you need it."
    ),
    "stressed": (
        "Give yourself permission to rest. Break tasks into smaller steps, "
        "and keep using this space to unload pressure before it builds up."
    ),
    "sad": (
        "Your feelings matter. Keep writing when you can, stay connected with people you trust, "
        "and be gentle with yourself as things settle."
    ),
    "angry": (
        "Notice what triggered the intensity, then choose a calming outlet — a walk, journaling, "
        "or talking it through. You do not have to carry it alone."
    ),
    "happy": (
        "Hold onto what supported this brighter mood. Capturing those moments in your journal "
        "can help you return to them on harder days."
    ),
    "calm": (
        "Steady moments are worth protecting. Keep the habits that help you feel grounded, "
        "and check in with yourself regularly."
    ),
    "hopeful": (
        "Hope is a powerful signal. Keep noting small steps forward — they compound into real change."
    ),
}

_DEFAULT_RECOMMENDATION = (
    "Continue journaling and remember that emotional changes are normal. "
    "Take breaks and seek support whenever necessary."
)


def _normalize(label: str | None) -> str:
    if not label:
        return "calm"
    key = label.strip().lower()
    return _FRIENDLY.get(key, key)


def build_emotion_timeline(db: Session, session_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(Message)
        .filter(Message.session_id == session_id, Message.role == "user")
        .order_by(Message.timestamp.asc())
        .all()
    )
    timeline: list[dict[str, Any]] = []
    for msg in rows:
        if not msg.emotion:
            continue
        timeline.append(
            {
                "emotion": msg.emotion,
                "confidence": msg.emotion_confidence,
                "mental_state": msg.mental_state,
                "content": (msg.content or "")[:280],
                "at": msg.timestamp.isoformat() if msg.timestamp else None,
            }
        )
    return timeline


# Intensity proxies for weighted dominant emotion (Phase F-5 / F-6)
_INTENSITY = {
    "crisis": 10.0,
    "grief": 9.0,
    "sad": 7.2,
    "anxious": 7.4,
    "fearful": 6.8,
    "stressed": 6.2,
    "angry": 5.5,
    "hopeless": 8.2,
    "hopeful": 2.5,
    "happy": 1.5,
    "warm": 2.0,
    "surprised": 2.0,
    "calm": 1.0,
}

_CONTEXT_IMPORTANCE = {
    "grief": 1.7,
    "sad": 1.45,
    "anxious": 1.4,
    "fearful": 1.35,
    "stressed": 1.35,
    "angry": 1.15,
    "hopeful": 1.0,
    "happy": 0.7,
    "calm": 0.5,
    "warm": 0.75,
    "surprised": 0.8,
}

_MENTAL_INTENSITY = {
    "crisis": 10.0,
    "depression": 8.5,
    "grief": 9.0,
    "anxiety": 7.4,
    "acute anxiety": 8.2,
    "fear": 6.8,
    "stress": 6.2,
    "anger": 5.5,
    "sadness": 7.0,
    "joy": 1.0,
    "stable": 1.0,
}

# Phase F-6 — significant life events boost session dominance
_SIGNIFICANT_EVENT_KW = (
    "cheated", "cheating", "betrayal", "betrayed", "heartbreak", "heartbroken",
    "breakup", "broke up", "left me for", "passed away", "passed on",
    "died", "funeral", "lost my", "lost someone", "grief", "grieving",
)

_FOLLOWUP_LIGHT_KW = (
    "what are your thoughts", "what do you think", "can you help",
    "what should i do", "tell me more", "why?", "why", "and then",
    "any advice", "thoughts?", "go on",
)


def _content_importance_multiplier(content: str | None) -> float:
    text = (content or "").strip().lower()
    if not text:
        return 1.0
    words = text.split()
    if any(k in text for k in _SIGNIFICANT_EVENT_KW):
        return 1.55
    if len(words) <= 8 and (
        text.endswith("?")
        or any(k in text for k in _FOLLOWUP_LIGHT_KW)
        or text in {"why", "ok", "okay", "yeah", "yes", "hmm", "and"}
    ):
        return 0.35
    if len(words) <= 4:
        return 0.55
    return 1.0


def _weighted_dominant(timeline: list[dict[str, Any]], normalized: list[str]) -> str:
    """
    Dominant emotion from intensity × confidence × recency × contextual importance.
    Significant events (heartbreak / betrayal / loss) outweigh short follow-ups.
    """
    if not normalized:
        return "calm"
    n = len(normalized)
    scores: dict[str, float] = {}
    for i, emo in enumerate(normalized):
        conf = timeline[i].get("confidence")
        try:
            conf_f = float(conf) if conf is not None else 0.55
        except (TypeError, ValueError):
            conf_f = 0.55
        conf_f = max(0.15, min(1.0, conf_f if conf_f <= 1 else conf_f / 100.0))

        recency = 0.35 + 0.65 * (i / max(n - 1, 1))
        intensity = _INTENSITY.get(emo, 3.0)
        mental = (timeline[i].get("mental_state") or "").strip().lower()
        if mental in _MENTAL_INTENSITY:
            intensity = max(intensity, _MENTAL_INTENSITY[mental])
        importance = _CONTEXT_IMPORTANCE.get(emo, 1.0)
        importance *= _content_importance_multiplier(timeline[i].get("content"))

        # Latest turn boost only for non-follow-up distress
        content_mult = _content_importance_multiplier(timeline[i].get("content"))
        if i == n - 1 and emo not in ("calm", "happy") and content_mult >= 0.9:
            recency *= 1.1

        weight = intensity * (0.45 + 0.55 * conf_f) * recency * importance
        scores[emo] = scores.get(emo, 0.0) + weight

    return max(scores.items(), key=lambda kv: kv[1])[0]


def _journey_narrative(normalized: list[str]) -> str:
    if not normalized:
        return (
            "This session was brief, so there is limited emotional data yet. "
            "Returning for another conversation will help build a clearer picture over time."
        )
    if len(normalized) == 1:
        return (
            f"Throughout this conversation you mainly felt {normalized[0]}. "
            "Staying present with that feeling is a meaningful form of self-awareness."
        )

    start = normalized[0]
    end = normalized[-1]
    mid = normalized[1:-1]
    if not mid:
        return (
            f"You began the conversation feeling {start}, and by the end you felt {end}."
        )

    unique_mid: list[str] = []
    for e in mid:
        if e not in unique_mid and e not in {normalized[0], normalized[-1]}:
            unique_mid.append(e)
        if len(unique_mid) >= 2:
            break

    mid_clause = ""
    if unique_mid:
        if len(unique_mid) == 1:
            mid_clause = f", later felt {unique_mid[0]}"
        else:
            mid_clause = f", moved through {unique_mid[0]} and {unique_mid[1]}"

    return (
        f"You began the conversation feeling {start}{mid_clause}, "
        f"and gradually became {end} near the end."
    )


def compute_session_emotion_summary(db: Session, session_id: str) -> dict[str, Any]:
    timeline = build_emotion_timeline(db, session_id)
    raw_emotions = [t["emotion"] for t in timeline]
    normalized = [_normalize(e) for e in raw_emotions]

    if normalized:
        dominant = _weighted_dominant(timeline, normalized)
    else:
        dominant = "calm"

    transitions = 0
    for i in range(1, len(normalized)):
        if normalized[i] != normalized[i - 1]:
            transitions += 1

    recommendation = _RECOMMENDATIONS.get(dominant, _DEFAULT_RECOMMENDATION)

    return {
        "session_id": session_id,
        "dominant_emotion": dominant,
        "emotion_transitions": transitions,
        "journey": _journey_narrative(normalized),
        "recommendation": recommendation,
        "emotion_timeline": timeline,
    }


def end_chat_session(db: Session, session: ChatSession, user_id: str) -> dict[str, Any]:
    """Mark session ended and return emotional summary from stored analyses.

    Idempotent: re-ending an already-closed session returns the same summary
    without clearing messages (Phase F-4 continuous chat).
    """
    from datetime import datetime, timezone

    summary = compute_session_emotion_summary(db, session.id)

    if session.ended_at is None:
        session.ended_at = datetime.now(timezone.utc)
    if not session.summary:
        session.summary = (
            f"Dominant emotion: {summary['dominant_emotion']}. "
            f"{summary['journey']} "
            f"Recommendation: {summary['recommendation']}"
        )
    db.commit()
    invalidate_summary_cache(user_id=user_id, session_id=session.id)
    ended = session.ended_at
    summary["ended_at"] = ended.isoformat() if ended else None
    summary["recommendation"] = summary.get("recommendation") or ""
    return summary
