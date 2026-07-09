"""Backward-compatible shim — logic lives in emotion_pipeline.py."""

from app.emotion_pipeline import apply_emotion_context_rules, finalize_emotion_analysis

__all__ = ["apply_emotion_context_rules", "finalize_emotion_analysis"]
