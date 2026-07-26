"""Backward-compatible shim — logic lives in emotion_pipeline.py."""

from app.emotion_pipeline import (
    SessionEmotionState,
    apply_emotion_context_rules,
    build_conversation_emotion_context,
    build_emotion_trajectory_prompt_note,
    compute_session_emotion_state,
    finalize_emotion_analysis,
)

__all__ = [
    "SessionEmotionState",
    "apply_emotion_context_rules",
    "build_conversation_emotion_context",
    "build_emotion_trajectory_prompt_note",
    "compute_session_emotion_state",
    "finalize_emotion_analysis",
]
