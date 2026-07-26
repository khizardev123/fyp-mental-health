"""Post-inference emotion label refinement — no retraining required."""

import re
from typing import Any

# Linguistic patterns
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
_CHRONIC_DEPRESSION_KW = (
    "hopeless", "empty inside", "no motivation", "can't get out of bed",
    "worthless", "suicidal", "want to die", "anhedonia", "never happy anymore",
)
_LONELY_KW = (
    "lonely", "loneliness", "alone", "no friends", "isolated", "isolation",
    "disconnected", "left out", "emptiness", "empty inside", "homesick",
    "homesickness", "hopeless", "no hope", "burnout", "burned out", "burnt out",
    "emotionally exhausted", "emotional exhaustion", "drained", "worn out",
)


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(k in text for k in keywords)


def apply_emotion_context_rules(
    text: str,
    top_label: str,
    all_scores: dict[str, float],
    confidence: float,
) -> tuple[str, dict[str, float], float, dict[str, Any]]:
    """
    Refine ML labels using linguistic context.
    Returns (top_label, all_scores, confidence, meta).
    """
    text_lower = text.lower()
    meta: dict[str, Any] = {"rules_applied": []}
    severity_cap: int | None = None

    # 1. Negated positive affect → sadness, never joy
    if _NEGATED_POSITIVE.search(text_lower):
        if top_label == "joy" or all_scores.get("joy", 0) > 0.25:
            top_label = "sadness"
            all_scores = dict(all_scores)
            all_scores["joy"] = min(all_scores.get("joy", 0), 0.1)
            all_scores["depression"] = max(all_scores.get("depression", 0), 0.35)
            confidence = max(all_scores.get("depression", 0), confidence)
            severity_cap = 5
            meta["rules_applied"].append("negated_positive→sadness")

    # 2. Exam-related stress → stress/anxiety, not depression
    exam_ctx = _has_any(text_lower, _EXAM_KW)
    stress_ctx = _has_any(text_lower, _STRESS_KW)
    failure_ctx = _has_any(text_lower, _FAILURE_KW)
    chronic = _has_any(text_lower, _CHRONIC_DEPRESSION_KW)

    if exam_ctx and (stress_ctx or failure_ctx) and not chronic:
        all_scores = dict(all_scores)
        if top_label in ("depression", "normal", "joy", "grief"):
            top_label = "anxiety" if stress_ctx and all_scores.get("anxiety", 0) >= all_scores.get("stress", 0) else "stress"
            all_scores["stress"] = max(all_scores.get("stress", 0), 0.55)
            all_scores["anxiety"] = max(all_scores.get("anxiety", 0), 0.45)
            all_scores["depression"] = min(all_scores.get("depression", 0), 0.35)
            confidence = max(all_scores.get(top_label, 0), confidence)
            severity_cap = 6
            meta["rules_applied"].append("exam_stress→stress/anxiety")

    # 3. Academic failure → stress/disappointment, including when ML says stable
    if failure_ctx and (exam_ctx or _has_any(text_lower, ("school", "class", "course", "subject", "grade", "semester"))) and not chronic:
        all_scores = dict(all_scores)
        if top_label in ("depression", "normal", "joy", "anger", "sadness"):
            top_label = "stress"
            all_scores["stress"] = max(all_scores.get("stress", 0), 0.5)
            all_scores["depression"] = min(all_scores.get("depression", 0), 0.35)
            confidence = all_scores.get("stress", confidence)
            severity_cap = 6
            meta["rules_applied"].append("academic_failure→stress")

    # 4. Situational stress ≠ clinical depression
    if top_label == "depression" and not chronic:
        all_scores = dict(all_scores)
        stress_score = all_scores.get("stress", 0)
        dep_score = all_scores.get("depression", 0)
        situational = stress_ctx or exam_ctx or _has_any(text_lower, ("overwhelm", "burnout", "deadline", "pressure", "busy"))
        if situational and stress_score >= dep_score * 0.65:
            top_label = "anxiety" if all_scores.get("anxiety", 0) > stress_score else "stress"
            confidence = all_scores.get(top_label, confidence)
            severity_cap = min(severity_cap or 10, 6)
            meta["rules_applied"].append("stress≠depression")

    # Loneliness / isolation / burnout — avoid Stable unless contradicted
    if _has_any(text_lower, _LONELY_KW) and top_label in ("normal", "joy"):
        all_scores = dict(all_scores)
        if _has_any(text_lower, ("burnout", "burned out", "burnt out", "emotionally exhausted", "drained")):
            top_label = "stress"
            all_scores["stress"] = max(all_scores.get("stress", 0), 0.55)
            meta["rules_applied"].append("burnout→stress")
        elif _has_any(text_lower, ("hopeless", "empty inside", "emptiness", "no hope")):
            top_label = "sadness"
            all_scores["sadness"] = max(all_scores.get("sadness", 0), 0.5)
            all_scores["depression"] = max(all_scores.get("depression", 0), 0.4)
            meta["rules_applied"].append("hopeless→sadness")
        else:
            top_label = "sadness"
            all_scores["sadness"] = max(all_scores.get("sadness", 0), 0.5)
            meta["rules_applied"].append("loneliness→sadness")
        confidence = max(all_scores.get(top_label, 0), confidence)
        severity_cap = min(severity_cap or 10, 7)

    if severity_cap is not None:
        meta["severity_cap"] = severity_cap

    return top_label, all_scores, confidence, meta
