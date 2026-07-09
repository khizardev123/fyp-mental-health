"""
Unified emotion refinement pipeline — single source of truth for dashboard, avatar, and assessment.
Applied once after ML analysis in avatar-service.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_NEGATED_POSITIVE = re.compile(
    r"\b(not|never|no longer|isn't|aren't|wasn't|weren't|dont|don't|cannot|can't)\s+"
    r"(happy|joyful|good|fine|okay|ok|great|well|better)\b"
    r"|\bnot feeling (good|great|happy|well|okay)\b"
    r"|\b(unhappy|not happy|not good)\b",
    re.IGNORECASE,
)

_EXAM_KW = (
    "exam", "exams", "test", "midterm", "finals", "final exam",
    "studying", "study", "deadline", "assignment", "coursework", "semester",
)
_STRESS_KW = (
    "stress", "stressed", "overwhelm", "overwhelmed", "worried", "worry",
    "anxious", "anxiety", "nervous", "pressure", "can't focus", "cannot focus",
    "panic", "burnout", "burned out",
)
_FAILURE_KW = (
    "fail", "failed", "flunk", "bad grade", "didn't pass", "did not pass",
    "low mark", "low score", "failing",
)
_ACADEMIC_KW = ("school", "class", "course", "subject", "grade", "semester", "exam", "exams")
_UPCOMING_EXAM_KW = (
    "next week", "tomorrow", "soon", "coming up", "this week", "in a few days",
    "next month", "approaching",
)

DISPLAY_NAMES = {
    "crisis": "Crisis",
    "depression": "Depression",
    "anxiety": "Anxiety",
    "grief": "Grief",
    "anger": "Anger",
    "fear": "Fear",
    "stress": "Stress",
    "joy": "Joy",
    "normal": "Stable",
    "sadness": "Sadness",
}

# Primary emotion label shown in dashboard (aligned with mental state)
LABEL_TO_EMOTION = {
    "crisis": "sadness",
    "depression": "sadness",
    "anxiety": "anxiety",
    "grief": "sadness",
    "anger": "anger",
    "fear": "fear",
    "stress": "stress",
    "joy": "joy",
    "normal": "neutral",
    "sadness": "sadness",
}

SEVERITY_WEIGHTS = {
    "crisis": 10,
    "depression": 8,
    "anxiety": 7,
    "grief": 7,
    "anger": 6,
    "fear": 6,
    "stress": 5,
    "sadness": 4,
    "normal": 1,
    "joy": 0,
}

CLASS_TAGS = {
    "crisis": ["acute distress", "crisis indicators"],
    "depression": ["low mood", "hopelessness"],
    "anxiety": ["worry", "nervousness"],
    "stress": ["overwhelm", "pressure", "academic pressure"],
    "grief": ["loss", "sadness"],
    "anger": ["frustration", "irritability"],
    "fear": ["dread", "avoidance"],
    "joy": ["contentment", "positivity"],
    "normal": ["stable", "balanced"],
    "sadness": ["low mood", "disappointment"],
}


def _has(text: str, kws: tuple[str, ...]) -> bool:
    return any(k in text for k in kws)


def _compute_severity(label: str, crisis_prob: float, all_scores: dict[str, float]) -> int:
    base = SEVERITY_WEIGHTS.get(label, 3)
    crisis_signal = all_scores.get("crisis", 0.0) * 5
    joy_dampen = all_scores.get("joy", 0.0) * 3
    severity = base + crisis_signal - joy_dampen
    return max(1, min(10, round(severity)))


def _semantic_summary(label: str, severity: int, text: str) -> str:
    text_lower = text.lower()
    if label == "stress" and _has(text_lower, _FAILURE_KW):
        return (
            f"Academic disappointment or setback (severity {severity}/10). "
            "This reads as situational stress rather than clinical depression."
        )
    if label in ("stress", "anxiety") and _has(text_lower, _EXAM_KW):
        return (
            f"Exam-related stress detected (severity {severity}/10). "
            "Academic pressure is present - practical coping and pacing may help."
        )
    summaries = {
        "crisis": f"Severe psychological distress with crisis indicators (severity {severity}/10). Immediate support is recommended.",
        "depression": f"Depressive patterns including low mood (severity {severity}/10). Professional support may be beneficial.",
        "anxiety": f"Anxiety, worry, or nervous tension (severity {severity}/10). Grounding strategies may help.",
        "stress": f"Situational stress or overwhelm (severity {severity}/10). Rest and stress management are recommended.",
        "grief": f"Grief or significant loss (severity {severity}/10). Compassionate support is appropriate.",
        "anger": f"Anger or frustration (severity {severity}/10). De-escalation support may help.",
        "fear": f"Fear or dread (severity {severity}/10). Reassurance and safety techniques are helpful.",
        "sadness": f"Low mood or sadness without strong depressive severity (severity {severity}/10). Supportive listening is appropriate.",
        "joy": f"Positive emotional tone (severity {severity}/10). Continue supportive engagement.",
        "normal": f"Emotionally stable presentation (severity {severity}/10). Routine wellness check-in is appropriate.",
    }
    return summaries.get(label, f"Emotional state: {DISPLAY_NAMES.get(label, label)} (severity {severity}/10).")


def _apply_context_rules(
    text: str, label: str, all_scores: dict[str, float],
) -> tuple[str, dict[str, float], int | None, list[str]]:
    """Return refined label, scores, optional severity cap, rules applied."""
    text_lower = text.lower()
    rules: list[str] = []
    scores = dict(all_scores)
    severity_cap: int | None = None

    exam = _has(text_lower, _EXAM_KW)
    stress = _has(text_lower, _STRESS_KW)
    failure = _has(text_lower, _FAILURE_KW)
    academic = _has(text_lower, _ACADEMIC_KW)
    chronic = _has(text_lower, (
        "hopeless", "empty inside", "no motivation", "can't get out of bed",
        "worthless", "suicidal", "want to die", "anhedonia", "never happy anymore",
    ))

    if _NEGATED_POSITIVE.search(text_lower) and (label == "joy" or scores.get("joy", 0) > 0.25):
        label = "sadness"
        scores["joy"] = min(scores.get("joy", 0), 0.1)
        scores["depression"] = max(scores.get("depression", 0), 0.35)
        severity_cap = 5
        rules.append("negated_positive->sadness")

    if exam and _has(text_lower, ("pressure", "pressured")) and not chronic:
        if label in ("depression", "normal", "joy", "sadness", "grief", "anger"):
            label = "stress"
            scores["stress"] = max(scores.get("stress", 0), 0.55)
            scores["depression"] = min(scores.get("depression", 0), 0.3)
            severity_cap = 6
            rules.append("exam_pressure->stress")

    if exam and (stress or failure) and not chronic:
        if label in ("depression", "normal", "joy", "grief", "anger", "sadness"):
            label = "anxiety" if stress and scores.get("anxiety", 0) >= scores.get("stress", 0) else "stress"
            scores["stress"] = max(scores.get("stress", 0), 0.55)
            scores["anxiety"] = max(scores.get("anxiety", 0), 0.4)
            scores["depression"] = min(scores.get("depression", 0), 0.3)
            severity_cap = 6
            rules.append("exam_stress->stress/anxiety")

    if exam and not chronic and not failure:
        upcoming = _has(text_lower, _UPCOMING_EXAM_KW) or _has(text_lower, ("worried", "nervous", "scared"))
        if upcoming and label in ("depression", "normal", "joy", "sadness", "grief"):
            label = "anxiety" if scores.get("anxiety", 0) >= scores.get("stress", 0) else "stress"
            scores["stress"] = max(scores.get("stress", 0), 0.45)
            scores["anxiety"] = max(scores.get("anxiety", 0), 0.35)
            scores["depression"] = min(scores.get("depression", 0), 0.3)
            severity_cap = min(severity_cap or 10, 6)
            rules.append("upcoming_exam->stress/anxiety")

    if failure and academic and not chronic:
        if label in ("depression", "normal", "joy", "anger", "sadness"):
            label = "stress"
            scores["stress"] = max(scores.get("stress", 0), 0.5)
            scores["depression"] = min(scores.get("depression", 0), 0.35)
            severity_cap = 6
            rules.append("academic_failure->stress")

    if label == "depression" and not chronic:
        situational = stress or exam or _has(text_lower, ("overwhelm", "burnout", "deadline", "pressure", "busy"))
        if situational and scores.get("stress", 0) >= scores.get("depression", 0) * 0.55:
            label = "anxiety" if scores.get("anxiety", 0) > scores.get("stress", 0) else "stress"
            severity_cap = min(severity_cap or 10, 6)
            rules.append("stress_not_depression")

    if severity_cap is not None:
        pass  # cap applied after severity recompute

    return label, scores, severity_cap, rules


def finalize_emotion_analysis(message: str, analysis: dict[str, Any]) -> dict[str, Any]:
    """Synchronize all emotion fields from ML output + context rules."""
    # Drop stale ai-service display fields so dict(analysis) cannot preserve them
    stale_keys = (
        "raw_label", "emotion", "mental_state", "severity_rating", "semantic_summary",
        "assessment", "tags", "final_emotion", "final_mental_state",
        "emotion_rules_applied", "unified", "emotion_compat", "mental_health",
    )
    clean = {k: v for k, v in analysis.items() if k not in stale_keys}

    ml_label = clean.get("ml_raw_label") or "normal"
    ml_confidence = float(clean.get("confidence") or 0.0)
    ml_scores = dict(clean.get("all_scores") or {})
    crisis_prob = float(clean.get("crisis_probability") or 0.0)

    label = ml_label
    scores = ml_scores
    label, scores, severity_cap, rules = _apply_context_rules(message, label, scores)

    severity = _compute_severity(label, crisis_prob, scores)
    if severity_cap is not None:
        severity = min(severity, severity_cap)

    emotion = LABEL_TO_EMOTION.get(label, "neutral")
    mental_state = DISPLAY_NAMES.get(label, label.capitalize())
    summary = _semantic_summary(label, severity, message)
    tags = list(CLASS_TAGS.get(label, ["stable"]))
    if _has(message.lower(), _EXAM_KW) and "academic pressure" not in tags:
        tags.append("academic pressure")
    if _has(message.lower(), _FAILURE_KW) and "disappointment" not in tags:
        tags.append("disappointment")

    logger.info(
        "[Emotion] ml=%s → %s | emotion=%s | mental_state=%s | severity=%s",
        ml_label,
        label,
        emotion,
        mental_state,
        severity,
    )

    result = dict(clean)
    result.update({
        "ml_raw_label": ml_label,
        "ml_confidence": ml_confidence,
        "raw_label": label,
        "mental_state": mental_state,
        "emotion": emotion,
        "severity_rating": severity,
        "all_scores": scores,
        "semantic_summary": summary,
        "tags": tags[:5],
        "emotion_rules_applied": rules,
        "final_emotion": emotion,
        "final_mental_state": mental_state,
        "assessment": summary,
    })

    # Hard sync — no field may retain stale ML values after rules
    result["emotion"] = LABEL_TO_EMOTION.get(result["raw_label"], "neutral")
    result["mental_state"] = DISPLAY_NAMES.get(result["raw_label"], result["raw_label"].capitalize())
    result["final_emotion"] = result["emotion"]
    result["final_mental_state"] = result["mental_state"]
    result["severity_rating"] = _compute_severity(result["raw_label"], crisis_prob, result["all_scores"])
    if severity_cap is not None:
        result["severity_rating"] = min(result["severity_rating"], severity_cap)
    result["semantic_summary"] = _semantic_summary(result["raw_label"], result["severity_rating"], message)
    result["assessment"] = result["semantic_summary"]
    result["tags"] = list(CLASS_TAGS.get(result["raw_label"], ["stable"]))[:5]
    if _has(message.lower(), _EXAM_KW) and "academic pressure" not in result["tags"]:
        result["tags"].append("academic pressure")
    if _has(message.lower(), _FAILURE_KW) and "disappointment" not in result["tags"]:
        result["tags"].append("disappointment")
    result["tags"] = result["tags"][:5]

    result.pop("unified", None)
    result["avatar_emotion_hint"] = _avatar_from_emotion(result["emotion"], result["raw_label"])
    return result


def _avatar_from_emotion(emotion: str, label: str) -> str:
    if label in ("stress", "anxiety") or emotion in ("stress", "anxiety", "fear"):
        return "anxious"
    if emotion in ("sadness",) or label in ("depression", "grief", "sadness"):
        return "sad"
    if emotion == "joy":
        return "happy"
    if emotion == "anger":
        return "angry"
    return "neutral"


def apply_emotion_context_rules(message: str, analysis: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible entry point used by chat_service."""
    if "ml_raw_label" not in analysis:
        analysis = dict(analysis)
        analysis["ml_raw_label"] = analysis.get("raw_label")
    return finalize_emotion_analysis(message, analysis)
