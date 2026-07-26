"""Emotion fusion: text + optional face cues for LLM prompt context."""

import logging

logger = logging.getLogger(__name__)

FACE_CONFIDENCE_THRESHOLD = 0.25
AVATAR_STATES = ("happy", "sad", "angry", "anxious", "neutral")

TEXT_ALIASES = {
    "joy": "happy",
    "happy": "happy",
    "sadness": "sad",
    "sad": "sad",
    "grief": "sad",
    "depression": "sad",
    "anger": "angry",
    "angry": "angry",
    "fear": "anxious",
    "anxiety": "anxious",
    "anxious": "anxious",
    "stress": "anxious",
    "neutral": "neutral",
    "normal": "neutral",
}


def normalize_emotion(emotion: str | None) -> str:
    if not emotion:
        return "neutral"
    key = emotion.lower().strip()
    return TEXT_ALIASES.get(key, "neutral")


def fuse_emotions(
    text_emotion: str,
    face_emotion: str | None = None,
    face_confidence: float = 0.0,
    *,
    session_state: dict | None = None,
) -> dict:
    """
    Weighted fusion: text 80%, face 20%.
    If webcam disabled / low confidence, text only.
    """
    text_state = normalize_emotion(text_emotion)
    face_state = normalize_emotion(face_emotion) if face_emotion else None

    if not face_state or face_confidence < FACE_CONFIDENCE_THRESHOLD:
        result = {
            "text_emotion": text_state,
            "face_emotion": face_state,
            "face_confidence": face_confidence,
            "final_avatar_emotion": text_state,
            "fusion_active": False,
            "fusion_weights": {"text": 1.0, "face": 0.0},
        }
        if session_state and text_state == "neutral":
            strength = float(session_state.get("continuity_strength") or 0.0)
            dominant = session_state.get("dominant_label")
            if strength >= 0.45 and dominant in ("stress", "anxiety", "sadness", "fear"):
                result["final_avatar_emotion"] = normalize_emotion(dominant)
                result["session_continuity_nudge"] = True
        return result

    # Score vector over avatar states
    scores = {s: 0.0 for s in AVATAR_STATES}
    scores[text_state] += 0.8
    scores[face_state] += 0.2 * face_confidence

    final = max(scores, key=scores.get)
    result = {
        "text_emotion": text_state,
        "face_emotion": face_state,
        "face_confidence": face_confidence,
        "final_avatar_emotion": final,
        "fusion_active": True,
        "fusion_weights": {"text": 0.8, "face": 0.2},
        "scores": scores,
    }
    return result


def build_fusion_prompt_context(
    *,
    message: str,
    text_emotion: str,
    face_emotion: str | None,
    face_confidence: float,
    fusion: dict,
) -> str | None:
    """
    Natural-language note for the LLM when face cues disagree with or reinforce text.
    """
    if not fusion.get("fusion_active"):
        return None

    text_norm = normalize_emotion(text_emotion)
    face_norm = normalize_emotion(face_emotion)
    short_msg = (message or "").strip()[:120]

    if text_norm == face_norm:
        return (
            f"Expression note: The user's words ({short_msg!r}) and facial cues both suggest "
            f"{text_norm}. Respond with aligned warmth."
        )

    # Mismatch — e.g. "I'm fine" + sad face
    return (
        f"Expression note: The user wrote {short_msg!r}, which reads as {text_norm}, "
        f"but their facial expression suggests {face_norm} (confidence {face_confidence:.0%}). "
        f"If appropriate, gently acknowledge that their expression may not fully match their words."
    )


def build_session_emotion_fusion_note(session_state: dict | None) -> str | None:
    """Optional note when session trajectory suggests ongoing distress but current text is neutral."""
    if not session_state:
        return None
    strength = float(session_state.get("continuity_strength") or 0.0)
    if strength < 0.35:
        return None
    trajectory = session_state.get("summary_line") or ""
    trend = session_state.get("trend") or "stable"
    if not trajectory:
        return None
    return (
        f"{trajectory} Session tone is {trend}. "
        "If the latest message is brief or vague, acknowledge the ongoing thread before shifting topic."
    )
