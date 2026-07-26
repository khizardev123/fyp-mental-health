"""
Unified emotion refinement pipeline — single source of truth for dashboard, avatar, and assessment.
Applied once after ML analysis in avatar-service.

Phase F-5: high-priority contextual rules + emotional continuity from recent user turns.
Does not call ML again — refinement is local string/score logic only.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.memory_retrieval import is_memory_recall_query

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

# Phase F-5 — high-priority emotional themes
_HEARTBREAK_KW = (
    "heartbreak", "heartbroken", "broken heart", "breakup", "break up", "broke up",
    "dumped me", "left me for", "cheated", "cheating", "cheat on", "betrayed",
    "betrayal", "unfaithful", "affair", "ex boyfriend", "ex girlfriend",
    "my partner left", "ended our relationship", "ended the relationship",
)
_GRIEF_KW = (
    "grief", "grieving", "mourning", "mourn", "passed away", "passed on",
    "funeral", "died", "death of", "lost my mom", "lost my dad", "lost my mother",
    "lost my father", "lost my parent", "lost my friend", "lost someone",
    "in memory of", "bereaved", "bereavement",
)
_PANIC_KW = (
    "panic attack", "panicking", "having a panic", "i'm panicking", "im panicking",
    "can't breathe", "cannot breathe", "cant breathe", "can't catch my breath",
    "hyperventilat", "heart racing", "my heart is racing", "heart is pounding",
    "chest tight", "chest is tight", "spiraling", "spiralling",
    "freaking out", "freak out", "out of control", "everything feels out of control",
    "losing control", "acute anxiety",
)
_BURNOUT_KW = (
    "burnout", "burned out", "burnt out", "emotionally exhausted",
    "emotional exhaustion", "drained", "worn out", "can't cope", "cannot cope",
    "running on empty", "completely exhausted",
)
_HOPELESS_KW = (
    "hopeless", "no hope", "pointless", "nothing matters", "give up",
    "empty inside", "emptiness", "feel empty", "worthless", "no reason to",
)
_LONELY_KW = (
    "lonely", "loneliness", "alone", "no friends", "no one to talk",
    "isolated", "isolation", "disconnected", "left out", "nobody cares",
    "homesick", "homesickness", "miss home", "far from home",
    "academic pressure", "too much pressure",
) + _BURNOUT_KW + _HOPELESS_KW

_SEVERE_STRESS_KW = (
    "severe stress", "extreme stress", "so stressed", "stress is killing",
    "breaking point", "at my limit", "can't take it", "cannot take it",
    "too much pressure", "academic pressure", "pressure is too much",
)

# Clear recovery / contradiction — allows calm labels despite prior distress
_RECOVERY_KW = (
    "feeling better", "feel better", "much better", "feel much better",
    "i'm okay now", "im okay now", "i am okay now", "i'm finally okay", "im finally okay",
    "finally okay", "i'm fine now", "im fine now", "i am fine now",
    "resolved", "over it now", "moved on", "feeling hopeful",
    "i feel happy", "i'm happy", "im happy", "doing okay now", "things are better",
    "recovered", "feeling calm", "feel calm", "calm again", "feel calm again",
    "finally at peace", "feel at peace", "at peace", "relieved now", "feel relieved",
    "feel relaxed", "feeling relaxed", "more relaxed", "much more relaxed",
    "talking to my family helped", "talked with my family", "talked to my family",
    "family helped me", "feel okay again", "feeling okay again",
    "i feel okay now", "im feeling better", "i'm feeling better",
    "i've calmed down", "ive calmed down", "calmed down",
    "i'm feeling hopeful again", "im feeling hopeful again", "feeling hopeful again",
    "better now", "i'm better now", "im better now",
    "feel a bit better", "feeling a bit better", "a bit better", "somewhat better",
    "little better", "slightly better",
)

# Gradual recovery — soften distress one step; does not require full calm/joy wording
_PARTIAL_RECOVERY_KW = (
    "feel a bit better", "feeling a bit better", "a bit better", "somewhat better",
    "little better", "slightly better",
    "talked to my friend", "talked with my friend", "spoke to my friend",
    "talking to my friend", "called my friend", "my friend helped",
    "slowly improving", "improving slowly", "starting to improve", "getting better slowly",
    "calmer now", "i'm calmer", "im calmer", "i am calmer", "feeling calmer", "more calm",
    "a little calmer", "somewhat calmer",
)

# Strong recovery — maps to calm/joy in recovery_override
_FULL_RECOVERY_KW = tuple(
    kw for kw in _RECOVERY_KW if kw not in _PARTIAL_RECOVERY_KW
)

_RECOVERY_JOY_KW = (
    "happy", "joyful", "grateful", "hopeful", "excited", "at peace", "relieved",
)

# Clear positive affect — current message wins over session distress continuity
_POSITIVE_AFFECT_KW = (
    "thrilled", "excited", "so happy", "i'm happy", "im happy", "i am happy",
    "happy today", "got an a", "got an a+", "got a grade", "passed my", "passed the",
    "passed my exam", "passed the exam", "proud of", "i'm proud", "im proud",
    "grateful", "thankful", "relieved", "great news", "good news", "wonderful news",
    "internship offer", "so glad", "celebrat", "achievement", "i did it",
    "love cricket", "i love cricket", "favourite batsman", "favorite batsman",
    "i love football", "i love sport", "enjoy cricket", "looking forward to",
)

_POSITIVE_HOBBY_KW = (
    "cricket", "football", "soccer", "basketball", "tennis", "ipl", "hobby",
    "hobbies", "favourite", "favorite", "batsman", "player", "team",
)

_TOPIC_SHIFT_RE = re.compile(
    r"\b("
    r"anyway|anyhow|changing the subject|change of subject|change the topic|"
    r"by the way|btw|different topic|moving on|on another note|"
    r"off topic|random question|speaking of something else|new topic"
    r")\b",
    re.IGNORECASE,
)

# Domain buckets for implicit topic-shift detection (unrelated subject matter)
_DOMAIN_RELATIONSHIP = _HEARTBREAK_KW + _GRIEF_KW + (
    "lonely", "breakup", "relationship", "girlfriend", "boyfriend", "partner",
)
_DOMAIN_ACADEMIC = _EXAM_KW + (
    "fyp", "final year", "assignment", "coursework", "degree", "university", "uni",
    "serenemind", "deadline", "overwhelmed by",
)
_DOMAIN_WEATHER_OUTDOORS = (
    "weather", "hiking", "hike", "rain", "rainy", "sunny", "forecast", "temperature",
    "outside", "outdoors", "mountain", "trail",
)
_DOMAIN_HOBBY = _POSITIVE_HOBBY_KW + ("match", "game", "won", "watching")

# ML confidence above which the current turn should beat session continuity (when not a light follow-up)
_CURRENT_MESSAGE_PRIORITY_CONF = 0.62
_UNCERTAIN_ML_CONF = 0.68

_FOLLOWUP_RE = re.compile(
    r"^\s*("
    r"what (are|do) your thoughts|what (are|do) you think|your thoughts\??|"
    r"what should i do|what do i do|can you help( me)?|help me\??|"
    r"why\??|why is that|and then\??|go on|continue|any advice|"
    r"thoughts\??|really\??|seriously\??|idk|i don'?t know|"
    r"hmm+|ok\.?|okay\.?|yeah|yep|yes\??|right\??|same|"
    r"what now|and\??|so\??|tell me more"
    r")\s*$",
    re.IGNORECASE,
)

_CALM_LABELS = frozenset({"normal", "joy"})
_DISTRESS_EMOTIONS = frozenset({
    "sadness", "anxiety", "stress", "anger", "fear", "grief",
})

# Distress severity ladder for gradual escalation / recovery (joy/normal at base)
_DISTRESS_LADDER: tuple[str, ...] = (
    "normal",
    "joy",
    "stress",
    "anxiety",
    "fear",
    "sadness",
    "grief",
    "depression",
    "crisis",
)

_LADDER_INDEX = {label: idx for idx, label in enumerate(_DISTRESS_LADDER)}

_ESCALATION_KW = (
    "overwhelm", "overwhelmed", "worse", "getting worse", "can't cope", "cannot cope",
    "breaking down", "falling apart", "too much", "more anxious", "more stressed",
    "even worse", " spiraling", "spiralling",
)

# Mild wording — at most one ladder step, capped at anxiety (never fear+)
_MILD_ESCALATION_KW = (
    "harder", "getting harder", "it's getting harder", "its getting harder",
    "more difficult", "tougher",
)

_MILD_STRESS_KW = (
    "can't focus", "cannot focus", "cant focus", "trouble focusing", "hard to focus",
    "difficulty focusing", "can't concentrate", "cannot concentrate", "cant concentrate",
)

CONTINUITY_CONTEXT_LIMIT = 10


@dataclass
class SessionEmotionState:
    """Weighted emotional trajectory from recent user turns (soft prior, not a lock)."""

    trajectory: list[str] = field(default_factory=list)
    trajectory_labels: list[str] = field(default_factory=list)
    dominant_label: str | None = None
    trend: str = "stable"
    continuity_strength: float = 0.0
    summary_line: str = ""

    def has_history(self) -> bool:
        return bool(self.trajectory_labels)

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

_EMOTION_TO_LABEL = {
    "sadness": "sadness",
    "anxiety": "anxiety",
    "stress": "stress",
    "anger": "anger",
    "fear": "fear",
    "joy": "joy",
    "neutral": "normal",
    "calm": "normal",
}

_MENTAL_TO_LABEL = {
    "crisis": "crisis",
    "depression": "depression",
    "anxiety": "anxiety",
    "grief": "grief",
    "anger": "anger",
    "fear": "fear",
    "stress": "stress",
    "joy": "joy",
    "stable": "normal",
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
    if label == "sadness" and _has(text_lower, _HEARTBREAK_KW):
        return (
            f"Relationship hurt or betrayal themes (severity {severity}/10). "
            "Compassionate support and validation are appropriate."
        )
    if label == "grief" or _has(text_lower, _GRIEF_KW):
        return (
            f"Grief or significant loss (severity {severity}/10). "
            "Compassionate support is appropriate."
        )
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


def _has_recovery_signal(text_lower: str) -> bool:
    return _has(text_lower, _RECOVERY_KW) or _has(text_lower, _PARTIAL_RECOVERY_KW)


def _has_full_recovery_signal(text_lower: str) -> bool:
    return _has(text_lower, _FULL_RECOVERY_KW)


def _has_partial_recovery_signal(text_lower: str) -> bool:
    return _has(text_lower, _PARTIAL_RECOVERY_KW)


def _has_positive_affect_signal(text_lower: str) -> bool:
    """Joy, achievement, gratitude, pride, relief, or enthusiastic hobby interest."""
    if _NEGATED_POSITIVE.search(text_lower):
        return False
    if _has(text_lower, _POSITIVE_AFFECT_KW):
        return True
    if _has(text_lower, ("i love", "i really love", "i enjoy", "i like")) and _has(
        text_lower, _POSITIVE_HOBBY_KW
    ):
        return True
    return False


def _infer_topic_domain(text_lower: str) -> str | None:
    """Coarse domain tag for topic-shift comparison."""
    if _has(text_lower, _DOMAIN_RELATIONSHIP):
        return "relationship"
    if _has(text_lower, _DOMAIN_WEATHER_OUTDOORS):
        return "weather_outdoors"
    if _has(text_lower, _DOMAIN_HOBBY) and not _has(text_lower, _STRESS_KW + _EXAM_KW):
        return "hobby"
    if _has(text_lower, _DOMAIN_ACADEMIC):
        return "academic"
    if _has(text_lower, _PANIC_KW + _BURNOUT_KW):
        return "distress_acute"
    if _has(text_lower, _STRESS_KW):
        return "stress"
    return None


def _detect_topic_shift(
    text: str,
    conversation_context: list[dict[str, Any]] | None,
) -> bool:
    """
    Explicit pivot phrases or a clear domain jump from the prior user turn.
    When true, session emotional continuity is reduced for this turn.
    """
    if not conversation_context:
        return False
    text_lower = text.strip().lower()
    if _TOPIC_SHIFT_RE.search(text_lower):
        return True

    prior_content = ""
    for turn in reversed(conversation_context):
        content = (turn.get("content") or "").strip()
        if content:
            prior_content = content.lower()
            break
    if not prior_content:
        return False

    current_domain = _infer_topic_domain(text_lower)
    prior_domain = _infer_topic_domain(prior_content)
    if not current_domain or not prior_domain:
        return False
    if current_domain == prior_domain:
        return False
    # Distress domains may bleed into related stress; unrelated leisure pivots are shifts
    unrelated_pairs = {
        ("relationship", "weather_outdoors"),
        ("relationship", "hobby"),
        ("relationship", "academic"),
        ("academic", "hobby"),
        ("academic", "weather_outdoors"),
        ("stress", "hobby"),
        ("stress", "weather_outdoors"),
        ("distress_acute", "hobby"),
        ("distress_acute", "weather_outdoors"),
    }
    pair = (prior_domain, current_domain)
    return pair in unrelated_pairs


def _apply_positive_affect_priority(
    text_lower: str,
    label: str,
    scores: dict[str, float],
    ml_confidence: float,
    rules: list[str],
) -> tuple[str, dict[str, float]]:
    """Ensure clear joy / achievement / hobby enthusiasm is not pulled back to prior distress."""
    target = label
    if label not in _CALM_LABELS:
        if label in _DISTRESS_EMOTIONS or label == "depression":
            target = "joy" if _has(
                text_lower,
                ("thrilled", "excited", "proud", "got an a", "happy", "love cricket"),
            ) else "normal"
        else:
            target = label
    elif label == "normal" and (
        _has(text_lower, ("thrilled", "excited", "proud", "got an a"))
        or ml_confidence >= 0.55 and scores.get("joy", 0) >= scores.get("normal", 0)
    ):
        target = "joy"

    if target == label and label in _CALM_LABELS:
        rules.append("positive_affect_priority")
        return label, scores

    scores = dict(scores)
    scores[target] = max(scores.get(target, 0.0), max(0.68, ml_confidence, scores.get("joy", 0)))
    if target == "joy":
        for damp in ("stress", "anxiety", "sadness", "depression", "grief", "fear", "anger"):
            scores[damp] = min(scores.get(damp, 0.0), 0.28)
    rules.append("positive_affect_priority")
    return target, scores


def _has_strong_current_emotional_signal(
    text_lower: str,
    label: str,
    ml_confidence: float,
) -> bool:
    """Current message clearly expresses its own emotion — session prior should not override."""
    if _has_positive_affect_signal(text_lower):
        return True
    if label == "joy" and ml_confidence >= 0.55:
        return True
    if label not in _CALM_LABELS and ml_confidence >= _CURRENT_MESSAGE_PRIORITY_CONF:
        return True
    if label in _CALM_LABELS and ml_confidence >= _CURRENT_MESSAGE_PRIORITY_CONF:
        if not _is_context_light_followup(text_lower) and len(text_lower.split()) >= 4:
            return True
    return False


def _has_active_crisis_language(text_lower: str) -> bool:
    return _has(
        text_lower,
        (
            "suicidal", "want to die", "kill myself", "end my life",
            "self harm", "self-harm", "hurt myself",
        ),
    )


def _align_scores_with_label(
    label: str,
    scores: dict[str, float],
) -> tuple[dict[str, float], float]:
    """
    Phase F-6: make probability ranking match the refined label.
    The winning class must be the top score; confidence follows that score.
    """
    aligned = {k: float(v) for k, v in scores.items()}
    if label not in aligned:
        aligned[label] = 0.0

    others = [v for k, v in aligned.items() if k != label]
    peak_other = max(others) if others else 0.35
    # Winner must clearly lead the ranking shown in the UI
    winner = max(aligned.get(label, 0.0), min(0.92, peak_other + 0.12), 0.58)
    aligned[label] = winner

    for k, v in list(aligned.items()):
        if k == label:
            continue
        # Keep supporting related signals, but never above the refined winner
        if k in _CALM_LABELS and label not in _CALM_LABELS:
            aligned[k] = min(v, winner * 0.72)
        elif label in ("sadness", "grief", "depression") and k in ("sadness", "grief", "depression"):
            aligned[k] = min(v, winner - 0.04) if k != label else v
        else:
            aligned[k] = min(v, winner - 0.06)
        aligned[k] = max(0.0, aligned[k])

    # Final safety: nothing may meet or exceed the winner
    for k, v in list(aligned.items()):
        if k != label and v >= aligned[label]:
            aligned[k] = aligned[label] * 0.82

    confidence = float(aligned[label])
    return aligned, max(0.42, min(0.97, confidence))


def _apply_partial_recovery_gradual(
    text_lower: str,
    label: str,
    scores: dict[str, float],
    session: SessionEmotionState,
    prior_label: str | None,
    rules: list[str],
) -> tuple[str, dict[str, float]]:
    """
    Gradual recovery: one step down the distress ladder instead of full calm/joy.
    Reduces continuity pull while acknowledging improvement.
    """
    anchor = label
    for candidate in (session.dominant_label, prior_label):
        if candidate and candidate not in _CALM_LABELS:
            if _ladder_index(candidate) > _ladder_index(anchor):
                anchor = candidate
    target = _one_step_deescalate(anchor)
    scores = dict(scores)
    key = _score_key_for_label(target)
    scores[key] = max(scores.get(key, 0.0), 0.56)
    for damp in ("sadness", "depression", "anxiety", "stress", "grief", "fear", "anger", "crisis"):
        if damp in scores and damp != key:
            scores[damp] = min(scores[damp], 0.48 if target not in _CALM_LABELS else 0.42)
    if target in _CALM_LABELS:
        scores["joy"] = max(scores.get("joy", 0.0), 0.28)
    rules.append(f"partial_recovery->{target}")
    return target, scores


def _apply_recovery_override(
    text: str,
    label: str,
    scores: dict[str, float],
    rules: list[str],
    *,
    conversation_context: list[dict[str, Any]] | None = None,
    session_state: SessionEmotionState | None = None,
) -> tuple[str, dict[str, float]]:
    """
    Explicit recovery language clears inherited distress toward Calm / Joy.
    Partial recovery uses gradual de-escalation; full recovery jumps to calm/joy.
    """
    text_lower = text.lower()
    if not _has_recovery_signal(text_lower):
        return label, scores
    if _has_active_crisis_language(text_lower):
        return label, scores
    if (
        _has(text_lower, _PANIC_KW)
        or _has(text_lower, _HEARTBREAK_KW)
        or _has(text_lower, _GRIEF_KW)
    ):
        return label, scores

    if _has_partial_recovery_signal(text_lower) and not _has_full_recovery_signal(text_lower):
        if any(r.startswith("partial_recovery") for r in rules):
            return label, scores
        session = session_state or compute_session_emotion_state(conversation_context)
        prior_label, _ = _prior_label_from_context(conversation_context)
        return _apply_partial_recovery_gradual(
            text_lower, label, scores, session, prior_label, rules,
        )

    target = "joy" if _has(text_lower, _RECOVERY_JOY_KW) else "normal"
    label = target
    scores = dict(scores)
    scores[target] = max(scores.get(target, 0.0), 0.72)
    if target == "normal":
        scores["joy"] = max(scores.get("joy", 0.0), 0.35)
    for damp in ("sadness", "depression", "anxiety", "stress", "grief", "fear", "anger", "crisis"):
        if damp in scores:
            scores[damp] = min(scores[damp], 0.32)
    rules.append(f"recovery_override->{target}")
    return label, scores


def _has_high_priority_distress(text_lower: str) -> bool:
    return (
        _has(text_lower, _HEARTBREAK_KW)
        or _has(text_lower, _GRIEF_KW)
        or _has(text_lower, _PANIC_KW)
        or _has(text_lower, _BURNOUT_KW)
        or _has(text_lower, _HOPELESS_KW)
        or _has(text_lower, _LONELY_KW)
        or _has(text_lower, _SEVERE_STRESS_KW)
        or (_has(text_lower, _EXAM_KW) and _has(text_lower, _STRESS_KW + ("pressure",)))
    )


def _is_context_light_followup(text: str) -> bool:
    """Short / clarifying turns that should inherit prior emotional context."""
    t = text.strip()
    if not t:
        return True
    if _has_high_priority_distress(t.lower()) or _has_recovery_signal(t.lower()):
        return False
    words = t.split()
    if len(words) <= 3:
        return True
    if len(t) <= 28 and "?" in t:
        return True
    if len(words) <= 12 and _FOLLOWUP_RE.match(t):
        return True
    if len(words) <= 10 and not _has(
        t.lower(),
        _STRESS_KW + _EXAM_KW + ("sad", "happy", "angry", "scared", "feel", "feeling"),
    ):
        # Generic prompts without explicit affect
        if any(p in t.lower() for p in (
            "thoughts", "advice", "help me", "what should", "what do you",
            "can you", "why", "tell me",
        )):
            return True
    return False


def _label_from_turn(turn: dict[str, Any]) -> str | None:
    """Map a stored user turn to a pipeline label."""
    emotion = (turn.get("emotion") or "").strip().lower()
    mental = (turn.get("mental_state") or "").strip().lower()
    if mental in _MENTAL_TO_LABEL:
        return _MENTAL_TO_LABEL[mental]
    if emotion in _EMOTION_TO_LABEL:
        return _EMOTION_TO_LABEL[emotion]
    if emotion in _DISTRESS_EMOTIONS:
        return emotion
    if emotion == "grief":
        return "grief"
    return None


def _ladder_index(label: str | None) -> int:
    if not label:
        return 0
    return _LADDER_INDEX.get(label, 3)


def _one_step_escalate(label: str, *, cap: str = "crisis") -> str:
    """Move at most one step up the distress ladder, never above cap."""
    idx = _ladder_index(label)
    cap_idx = _ladder_index(cap)
    if idx >= cap_idx:
        return label if _ladder_index(label) <= cap_idx else cap
    nxt = _DISTRESS_LADDER[min(idx + 1, len(_DISTRESS_LADDER) - 1)]
    if nxt in _CALM_LABELS and label not in _CALM_LABELS:
        return label
    if _ladder_index(nxt) > cap_idx:
        return cap if _ladder_index(cap) > idx else label
    return nxt if _ladder_index(nxt) > idx else label


def _one_step_deescalate(label: str) -> str:
    """Move one step toward calm (partial recovery), not generic ladder index."""
    if label in _CALM_LABELS:
        return label
    deescalate_map: dict[str, str] = {
        "crisis": "depression",
        "depression": "grief",
        "grief": "sadness",
        "sadness": "stress",
        "fear": "anxiety",
        "anxiety": "stress",
        "stress": "normal",
        "anger": "stress",
    }
    return deescalate_map.get(label, "normal")


def _escalation_cap_for_message(text_lower: str) -> str:
    """Max ladder label for continuity escalation from this message."""
    if _has(text_lower, _ESCALATION_KW):
        return "fear"
    if _has(text_lower, _MILD_ESCALATION_KW) or _has(text_lower, _MILD_STRESS_KW):
        return "anxiety"
    if _has(text_lower, _STRESS_KW):
        return "anxiety"
    return "anxiety"


def _continuity_escalation_target(session_label: str | None, text_lower: str) -> str | None:
    """One-step escalation from session tone when the current message warrants it."""
    if not session_label:
        return None
    cap = _escalation_cap_for_message(text_lower)
    has_signal = (
        _has(text_lower, _ESCALATION_KW)
        or _has(text_lower, _MILD_ESCALATION_KW)
        or _has(text_lower, _MILD_STRESS_KW)
        or _has(text_lower, _STRESS_KW)
    )
    if not has_signal:
        return None
    candidate = _one_step_escalate(session_label, cap=cap)
    if _ladder_index(candidate) > _ladder_index(session_label):
        return candidate
    return None


def _content_importance_multiplier(content: str | None) -> float:
    text = (content or "").strip().lower()
    if not text:
        return 1.0
    words = text.split()
    if any(k in text for k in ("cheated", "betrayal", "heartbreak", "passed away", "died", "lost my")):
        return 1.55
    if len(words) <= 8 and text.endswith("?"):
        if any(k in text for k in ("thoughts", "advice", "help me", "what should", "why")):
            return 0.35
    if len(words) <= 4:
        return 0.55
    return 1.0


def compute_session_emotion_state(
    conversation_context: list[dict[str, Any]] | None,
    *,
    window: int = CONTINUITY_CONTEXT_LIMIT,
) -> SessionEmotionState:
    """
    Build a weighted emotional trajectory from recent user turns.
    Acts as a soft prior — never hard-locks future states.
    """
    if not conversation_context:
        return SessionEmotionState()

    turns = conversation_context[-window:]
    trajectory_labels: list[str] = []
    trajectory: list[str] = []

    for turn in turns:
        lbl = _label_from_turn(turn)
        if not lbl:
            continue
        trajectory_labels.append(lbl)
        trajectory.append(DISPLAY_NAMES.get(lbl, lbl.replace("_", " ").title()))

    if not trajectory_labels:
        return SessionEmotionState()

    indices = [_ladder_index(l) for l in trajectory_labels]
    if len(indices) >= 2:
        delta = indices[-1] - indices[-2]
        if delta > 0:
            trend = "escalating"
        elif delta < 0:
            trend = "recovering"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Weighted dominant (recency + intensity); calm follow-ups weigh less
    intensity_map = {
        "crisis": 10.0, "depression": 8.0, "grief": 9.0, "sadness": 7.0,
        "anxiety": 7.0, "fear": 6.5, "stress": 6.0, "anger": 5.5,
        "normal": 1.0, "joy": 0.5,
    }
    scores: dict[str, float] = {}
    n = len(turns)
    for i, turn in enumerate(turns):
        lbl = _label_from_turn(turn)
        if not lbl:
            continue
        conf = float(turn.get("confidence") or turn.get("emotion_confidence") or 0.55)
        conf = max(0.15, min(1.0, conf if conf <= 1 else conf / 100.0))
        recency = 0.35 + 0.65 * (i / max(n - 1, 1))
        mult = _content_importance_multiplier(turn.get("content"))
        weight = intensity_map.get(lbl, 3.0) * (0.45 + 0.55 * conf) * recency * mult
        scores[lbl] = scores.get(lbl, 0.0) + weight

    dominant_label = max(scores.items(), key=lambda kv: kv[1])[0] if scores else trajectory_labels[-1]

    recent = trajectory_labels[-5:]
    distress_recent = sum(1 for l in recent if l not in _CALM_LABELS)
    if dominant_label in _CALM_LABELS or trend == "recovering":
        strength = max(0.0, 0.12 * distress_recent)
    else:
        strength = min(0.82, 0.22 + distress_recent * 0.11 + (0.08 if trend == "escalating" else 0.0))

    summary_line = ""
    if trajectory:
        summary_line = "Recent emotional journey: " + " → ".join(trajectory)

    return SessionEmotionState(
        trajectory=trajectory,
        trajectory_labels=trajectory_labels,
        dominant_label=dominant_label,
        trend=trend,
        continuity_strength=strength,
        summary_line=summary_line,
    )


def build_emotion_trajectory_prompt_note(
    session_state: SessionEmotionState | None,
    analysis: dict[str, Any],
) -> str | None:
    """Short trajectory block for the LLM analysis context."""
    if not session_state or not session_state.has_history():
        return None

    current_label = (
        analysis.get("raw_label")
        or analysis.get("ml_raw_label")
        or analysis.get("emotion")
    )
    current_ms = analysis.get("mental_state") or analysis.get("emotion")
    rules = analysis.get("emotion_rules_applied") or []
    is_recovery_turn = any(
        r.startswith("recovery_override") or r.startswith("partial_recovery")
        for r in rules
    )
    is_joy_turn = current_label == "joy" or analysis.get("emotion") == "joy"
    is_calm_current = current_label in _CALM_LABELS or analysis.get("emotion") in ("neutral", "joy")

    parts: list[str] = []

    if is_recovery_turn or is_joy_turn or (is_calm_current and session_state.trend == "recovering"):
        direction = current_ms or DISPLAY_NAMES.get(str(current_label), "calmer")
        parts.append(
            f"Current direction: the user is moving toward recovery or positive affect ({direction}). "
            "Treat their latest message as the primary emotional signal."
        )
        if session_state.summary_line:
            parts.append(f"Prior context (background only): {session_state.summary_line}")
        parts.append(
            "Do not carry forward stale session distress; acknowledge improvement or positive tone "
            "when their words show it."
        )
    else:
        parts.append(session_state.summary_line)
        if session_state.dominant_label and session_state.dominant_label not in _CALM_LABELS:
            tone = DISPLAY_NAMES.get(session_state.dominant_label, session_state.dominant_label)
            parts.append(f"Session emotional tone: {tone} ({session_state.trend}).")
        parts.append(
            "Continuity note: Prior turns provide context only — respond to the user's latest "
            "message first; do not assume they are still in distress if their words show recovery."
        )
        if current_ms:
            parts.append(f"Current emotion (this message): {current_ms}.")

    return " ".join(p for p in parts if p)


def _prior_label_from_context(conversation_context: list[dict[str, Any]] | None) -> tuple[str | None, float]:
    """Most recent non-empty user emotion → pipeline label + confidence."""
    if not conversation_context:
        return None, 0.0
    for turn in reversed(conversation_context):
        emotion = (turn.get("emotion") or "").strip().lower()
        mental = (turn.get("mental_state") or "").strip().lower()
        conf = float(turn.get("confidence") or turn.get("emotion_confidence") or 0.55)
        if mental in _MENTAL_TO_LABEL:
            label = _MENTAL_TO_LABEL[mental]
            if label not in _CALM_LABELS:
                return label, conf
        if emotion in _EMOTION_TO_LABEL:
            label = _EMOTION_TO_LABEL[emotion]
            if label not in _CALM_LABELS:
                return label, conf
        if emotion in _DISTRESS_EMOTIONS:
            return emotion if emotion != "grief" else "grief", conf
    # Fall back to last turn even if calm (for completeness)
    last = conversation_context[-1]
    emotion = (last.get("emotion") or "").strip().lower()
    mental = (last.get("mental_state") or "").strip().lower()
    conf = float(last.get("confidence") or 0.5)
    if mental in _MENTAL_TO_LABEL:
        return _MENTAL_TO_LABEL[mental], conf
    if emotion in _EMOTION_TO_LABEL:
        return _EMOTION_TO_LABEL[emotion], conf
    return None, 0.0


def _force_label(
    label: str,
    target: str,
    scores: dict[str, float],
    score_key: str,
    min_score: float,
    rules: list[str],
    rule_name: str,
    *,
    force_from_calm_only: bool = False,
    also_from: tuple[str, ...] = (),
) -> tuple[str, dict[str, float]]:
    """Override calm (and optional other) labels toward a high-priority target."""
    should = label in _CALM_LABELS or label in also_from
    if force_from_calm_only and label not in _CALM_LABELS:
        should = False
    if not should and label != target:
        # Still bump score evidence when keywords hit while already distressed
        scores[score_key] = max(scores.get(score_key, 0), min_score * 0.85)
        return label, scores
    if should or label == target:
        label = target
        scores[score_key] = max(scores.get(score_key, 0), min_score)
        if target == "sadness":
            scores["depression"] = max(scores.get("depression", 0), min(0.45, min_score))
        if target == "anxiety":
            scores["anxiety"] = max(scores.get("anxiety", 0), min_score)
        if target == "stress":
            scores["stress"] = max(scores.get("stress", 0), min_score)
        if target == "grief":
            scores["sadness"] = max(scores.get("sadness", 0), 0.45)
        rules.append(rule_name)
    return label, scores


def _apply_high_priority_rules(
    text_lower: str,
    label: str,
    scores: dict[str, float],
    rules: list[str],
    severity_cap: int | None,
) -> tuple[str, dict[str, float], int | None]:
    """High-priority themes must not remain Stable/Neutral without recovery evidence."""
    if _has_recovery_signal(text_lower):
        return label, scores, severity_cap

    if _has(text_lower, _HEARTBREAK_KW):
        label, scores = _force_label(
            label, "sadness", scores, "sadness", 0.62, rules,
            "heartbreak_betrayal->sadness",
            also_from=("anger", "stress", "normal", "joy"),
        )
        severity_cap = min(severity_cap or 10, 7)

    if _has(text_lower, _GRIEF_KW):
        label, scores = _force_label(
            label, "grief", scores, "sadness", 0.6, rules,
            "grief_loss->grief",
            also_from=("sadness", "depression", "normal", "joy", "stress"),
        )
        severity_cap = min(severity_cap or 10, 8)

    if _has(text_lower, _PANIC_KW):
        label, scores = _force_label(
            label, "anxiety", scores, "anxiety", 0.72, rules,
            "panic->acute_anxiety",
            also_from=("stress", "fear", "normal", "joy", "anger", "sadness"),
        )
        # Never leave anger / calm leading after panic language
        scores["anger"] = min(scores.get("anger", 0.0), 0.25)
        scores["normal"] = min(scores.get("normal", 0.0), 0.28)
        scores["joy"] = min(scores.get("joy", 0.0), 0.2)
        scores["anxiety"] = max(scores.get("anxiety", 0.0), 0.72)
        scores["fear"] = max(scores.get("fear", 0.0), 0.4)
        severity_cap = min(severity_cap or 10, 8)

    if _has(text_lower, _BURNOUT_KW):
        label, scores = _force_label(
            label, "stress", scores, "stress", 0.6, rules,
            "burnout->stress",
            also_from=("depression", "sadness", "normal", "joy"),
        )
        severity_cap = min(severity_cap or 10, 7)

    if _has(text_lower, _HOPELESS_KW):
        label, scores = _force_label(
            label, "sadness", scores, "sadness", 0.58, rules,
            "hopelessness->sadness",
            also_from=("normal", "joy", "stress"),
        )
        scores["depression"] = max(scores.get("depression", 0), 0.45)
        severity_cap = min(severity_cap or 10, 8)

    if _has(text_lower, _SEVERE_STRESS_KW) or (
        _has(text_lower, _EXAM_KW) and _has(text_lower, ("pressure", "overwhelm", "overwhelmed", "stressed"))
    ):
        if label in _CALM_LABELS or label in ("sadness", "anger"):
            label, scores = _force_label(
                label, "stress", scores, "stress", 0.58, rules,
                "severe_academic_stress->stress",
                also_from=("sadness", "anger", "normal", "joy"),
            )
            severity_cap = min(severity_cap or 10, 7)

    lonely = _has(text_lower, _LONELY_KW) and not _has(text_lower, _BURNOUT_KW) and not _has(text_lower, _HOPELESS_KW)
    if lonely and label in _CALM_LABELS:
        label, scores = _force_label(
            label, "sadness", scores, "sadness", 0.55, rules,
            "loneliness_isolation->sadness",
        )
        scores["anxiety"] = max(scores.get("anxiety", 0), 0.35)
        severity_cap = min(severity_cap or 10, 7)

    return label, scores, severity_cap


def _score_key_for_label(label: str) -> str:
    if label in ("sadness", "grief", "crisis"):
        return "sadness" if label != "depression" else "depression"
    if label in ("anxiety", "fear"):
        return "anxiety"
    if label == "stress":
        return "stress"
    if label == "depression":
        return "depression"
    return label


def _apply_escalation_cap(
    text_lower: str,
    label: str,
    scores: dict[str, float],
    rules: list[str],
) -> tuple[str, dict[str, float]]:
    """Cap mild wording at anxiety — do not jump to fear+ without stronger evidence."""
    if _ladder_index(label) <= _ladder_index("anxiety"):
        return label, scores
    has_mild = _has(text_lower, _MILD_ESCALATION_KW) or _has(text_lower, _MILD_STRESS_KW)
    has_strong = (
        _has(text_lower, _ESCALATION_KW)
        or _has(text_lower, _PANIC_KW)
        or _has(text_lower, _HEARTBREAK_KW)
        or _has(text_lower, _GRIEF_KW)
        or _has(text_lower, _HOPELESS_KW)
    )
    if not has_mild or has_strong:
        return label, scores
    cap = _escalation_cap_for_message(text_lower)
    if _ladder_index(label) <= _ladder_index(cap):
        return label, scores
    label = cap
    key = _score_key_for_label(label)
    scores = dict(scores)
    scores[key] = max(scores.get(key, 0), 0.55)
    scores["fear"] = min(scores.get("fear", 0), 0.32)
    rules.append(f"escalation_cap->{label}")
    return label, scores


def _apply_standalone_stress_keywords(
    text_lower: str,
    label: str,
    scores: dict[str, float],
    rules: list[str],
) -> tuple[str, dict[str, float]]:
    """Map clear stress/anxiety wording to distress labels without requiring exam context."""
    if label not in _CALM_LABELS:
        return label, scores
    if not _has(text_lower, _STRESS_KW):
        return label, scores
    if _has(text_lower, ("anxious", "anxiety", "panic", "worried", "nervous")):
        target = "anxiety"
        rule = "standalone_stress_kw->anxiety"
    else:
        target = "stress"
        rule = "standalone_stress_kw->stress"
    key = _score_key_for_label(target)
    scores[key] = max(scores.get(key, 0), 0.58)
    rules.append(rule)
    return target, scores


def _apply_emotional_continuity(
    text: str,
    label: str,
    scores: dict[str, float],
    conversation_context: list[dict[str, Any]] | None,
    rules: list[str],
    ml_confidence: float,
    session_state: SessionEmotionState | None = None,
) -> tuple[str, dict[str, float]]:
    """
    Soft emotional continuity from session trajectory + prior turns.
    Current message always has highest priority; crisis/recovery/positive-affect/topic-shift bypass blending.
    Session prior applies mainly to uncertain or context-light follow-ups.
    """
    if is_memory_recall_query(text):
        return label, scores

    text_lower = text.lower()
    if _has_active_crisis_language(text_lower):
        return label, scores
    if _has_recovery_signal(text_lower):
        return label, scores
    if _has_high_priority_distress(text_lower) and label not in _CALM_LABELS:
        return label, scores

    if _detect_topic_shift(text, conversation_context):
        rules.append("topic_shift_skip")
        return label, scores

    if _has_positive_affect_signal(text_lower):
        return _apply_positive_affect_priority(
            text_lower, label, scores, ml_confidence, rules,
        )

    if _has_strong_current_emotional_signal(text_lower, label, ml_confidence):
        if label == "joy":
            return _apply_positive_affect_priority(
                text_lower, label, scores, ml_confidence, rules,
            )
        rules.append("current_message_priority")
        return label, scores

    session = session_state or compute_session_emotion_state(conversation_context)
    prior_label, prior_conf = _prior_label_from_context(conversation_context)

    # Strong current distress signal — allow at most one-step escalation from session arc
    if label not in _CALM_LABELS and ml_confidence >= _CURRENT_MESSAGE_PRIORITY_CONF:
        if session.dominant_label:
            candidate = _continuity_escalation_target(session.dominant_label, text_lower)
            if candidate and _ladder_index(candidate) > _ladder_index(label):
                label = candidate
                key = _score_key_for_label(label)
                scores[key] = max(scores.get(key, 0), 0.56)
                rules.append(f"continuity_escalate->{label}")
        return label, scores

    strength = session.continuity_strength
    session_label = session.dominant_label or prior_label
    if not session_label or session_label in _CALM_LABELS or strength < 0.18:
        pass
    else:
        # Continuity influences uncertain predictions and context-light follow-ups only
        should_blend = (
            ml_confidence < _UNCERTAIN_ML_CONF
            and (
                label in _CALM_LABELS
                or _is_context_light_followup(text)
            )
        )
        if should_blend:
            target = session_label
            cap = _escalation_cap_for_message(text_lower)
            escalation = _continuity_escalation_target(session_label, text_lower)
            if escalation:
                target = escalation
            elif _has(text_lower, _STRESS_KW) and session.trend == "escalating":
                target = _one_step_escalate(session_label, cap=cap)
            elif _has(text_lower, _STRESS_KW):
                target = "stress" if _ladder_index("stress") >= _ladder_index(session_label) else session_label

            if label in _CALM_LABELS or ml_confidence < 0.62:
                if _ladder_index(target) >= _ladder_index(label):
                    key = _score_key_for_label(target)
                    scores[key] = max(scores.get(key, 0), max(0.52, prior_conf * 0.85 * strength))
                    if target != label:
                        rules.append(f"continuity_session_blend->{target}")
                        label = target

    # Context-light follow-ups: inherit prior when the latest message carries no new affect
    if prior_label and prior_label not in _CALM_LABELS:
        inherit = _is_context_light_followup(text) and label in _CALM_LABELS
        if inherit and label in _CALM_LABELS:
            key = _score_key_for_label(prior_label)
            scores[key] = max(scores.get(key, 0), max(0.5, prior_conf * 0.9))
            rules.append(f"continuity_inherit->{prior_label}")
            label = prior_label

    return label, scores


def _apply_context_rules(
    text: str,
    label: str,
    all_scores: dict[str, float],
    *,
    conversation_context: list[dict[str, Any]] | None = None,
    ml_confidence: float = 0.0,
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

    # Phase F-5 high-priority themes (before softer exam rules)
    label, scores, severity_cap = _apply_high_priority_rules(
        text_lower, label, scores, rules, severity_cap,
    )

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

    # Loneliness leftover path when not already handled as high-priority
    lonely = _has(text_lower, _LONELY_KW)
    if lonely and label in _CALM_LABELS:
        if _has(text_lower, _BURNOUT_KW):
            label = "stress"
            scores["stress"] = max(scores.get("stress", 0), 0.55)
            rules.append("burnout_exhaustion->stress")
        elif _has(text_lower, _HOPELESS_KW):
            label = "sadness"
            scores["sadness"] = max(scores.get("sadness", 0), 0.5)
            scores["depression"] = max(scores.get("depression", 0), 0.4)
            rules.append("hopeless_empty->sadness")
        else:
            label = "sadness"
            scores["sadness"] = max(scores.get("sadness", 0), 0.5)
            scores["anxiety"] = max(scores.get("anxiety", 0), 0.35)
            rules.append("loneliness_isolation->sadness")
        severity_cap = min(severity_cap or 10, 7)

    session_state = compute_session_emotion_state(conversation_context)

    label, scores = _apply_standalone_stress_keywords(text_lower, label, scores, rules)

    # Continuity — soft session prior after keyword rules; recovery applied after
    label, scores = _apply_emotional_continuity(
        text, label, scores, conversation_context, rules, ml_confidence,
        session_state=session_state,
    )

    # Phase F-6: explicit recovery clears inherited distress
    label, scores = _apply_recovery_override(
        text, label, scores, rules,
        conversation_context=conversation_context,
        session_state=session_state,
    )

    label, scores = _apply_escalation_cap(text_lower, label, scores, rules)

    return label, scores, severity_cap, rules


def finalize_emotion_analysis(
    message: str,
    analysis: dict[str, Any],
    conversation_context: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Synchronize all emotion fields from ML output + context rules (+ optional continuity)."""
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
    label, scores, severity_cap, rules = _apply_context_rules(
        message,
        label,
        scores,
        conversation_context=conversation_context,
        ml_confidence=ml_confidence,
    )

    # Phase F-6: ranking + confidence always reflect the refined decision
    scores, refined_confidence = _align_scores_with_label(label, scores)

    severity = _compute_severity(label, crisis_prob, scores)
    if severity_cap is not None:
        severity = min(severity, severity_cap)

    emotion = LABEL_TO_EMOTION.get(label, "neutral")
    mental_state = DISPLAY_NAMES.get(label, label.capitalize())
    if any(r.startswith("panic->") for r in rules):
        mental_state = "Acute Anxiety"
    summary = _semantic_summary(label, severity, message)
    tags = list(CLASS_TAGS.get(label, ["stable"]))
    mlower = message.lower()
    recall_turn = is_memory_recall_query(message)
    if _has(mlower, _EXAM_KW) and "academic pressure" not in tags and not recall_turn:
        tags.append("academic pressure")
    if _has(mlower, _FAILURE_KW) and "disappointment" not in tags:
        tags.append("disappointment")
    if _has(mlower, _HEARTBREAK_KW) and "relationship distress" not in tags:
        tags.append("relationship distress")
    if _has(mlower, _GRIEF_KW) and "loss" not in tags:
        tags.append("loss")
    if any(r.startswith("panic->") for r in rules) and "panic" not in tags:
        tags.append("panic")
    if _has(mlower, _LONELY_KW):
        for tag in ("loneliness", "social isolation", "emotional exhaustion"):
            if tag not in tags and _has(
                mlower,
                ("lonely", "alone", "isolated", "isolation", "disconnected")
                if tag != "emotional exhaustion"
                else ("burnout", "exhausted", "drained", "worn out"),
            ):
                tags.append(tag)

    logger.info(
        "[Emotion] ml=%s → %s | emotion=%s | mental_state=%s | severity=%s | conf=%.2f | rules=%s",
        ml_label,
        label,
        emotion,
        mental_state,
        severity,
        refined_confidence,
        rules,
    )

    result = dict(clean)
    result.update({
        "ml_raw_label": ml_label,
        "ml_confidence": ml_confidence,
        "confidence": refined_confidence,
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

    result["emotion"] = LABEL_TO_EMOTION.get(result["raw_label"], "neutral")
    if any(r.startswith("panic->") for r in rules):
        result["mental_state"] = "Acute Anxiety"
        result["final_mental_state"] = "Acute Anxiety"
    else:
        result["mental_state"] = DISPLAY_NAMES.get(result["raw_label"], result["raw_label"].capitalize())
        result["final_mental_state"] = result["mental_state"]
    result["final_emotion"] = result["emotion"]
    # Re-align after hard sync so ranking never drifts from label
    synced_scores, synced_conf = _align_scores_with_label(result["raw_label"], result["all_scores"])
    result["all_scores"] = synced_scores
    result["confidence"] = synced_conf
    result["severity_rating"] = _compute_severity(result["raw_label"], crisis_prob, result["all_scores"])
    if severity_cap is not None:
        result["severity_rating"] = min(result["severity_rating"], severity_cap)
    result["semantic_summary"] = _semantic_summary(result["raw_label"], result["severity_rating"], message)
    if any(r.startswith("panic->") for r in rules):
        result["semantic_summary"] = (
            f"Acute anxiety / panic symptoms (severity {result['severity_rating']}/10). "
            "Grounding and paced breathing may help; crisis pathways remain available if needed."
        )
    result["assessment"] = result["semantic_summary"]
    result["tags"] = list(CLASS_TAGS.get(result["raw_label"], ["stable"]))[:5]
    if _has(mlower, _EXAM_KW) and "academic pressure" not in result["tags"] and not recall_turn:
        result["tags"].append("academic pressure")
    if _has(mlower, _FAILURE_KW) and "disappointment" not in result["tags"]:
        result["tags"].append("disappointment")
    if _has(mlower, _HEARTBREAK_KW) and "relationship distress" not in result["tags"]:
        result["tags"].append("relationship distress")
    if _has(mlower, ("lonely", "loneliness", "alone", "isolated", "isolation", "disconnected")):
        if "loneliness" not in result["tags"]:
            result["tags"].append("loneliness")
    if _has(mlower, ("burnout", "burned out", "emotionally exhausted", "drained")):
        if "emotional exhaustion" not in result["tags"]:
            result["tags"].append("emotional exhaustion")
    if any(r.startswith("panic->") for r in rules) and "panic" not in result["tags"]:
        result["tags"].append("panic")
    result["tags"] = result["tags"][:5]

    result.pop("unified", None)
    result["avatar_emotion_hint"] = _avatar_from_emotion(result["emotion"], result["raw_label"])

    session_state = compute_session_emotion_state(conversation_context)
    if session_state.has_history():
        result["emotion_trajectory"] = session_state.trajectory
        result["emotion_trajectory_summary"] = session_state.summary_line
        result["session_emotion_trend"] = session_state.trend
        result["session_continuity_strength"] = session_state.continuity_strength

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


def apply_emotion_context_rules(
    message: str,
    analysis: dict[str, Any],
    conversation_context: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Backward-compatible entry point used by chat_service."""
    if "ml_raw_label" not in analysis:
        analysis = dict(analysis)
        analysis["ml_raw_label"] = analysis.get("raw_label")
    return finalize_emotion_analysis(message, analysis, conversation_context=conversation_context)


def build_conversation_emotion_context(prior_messages: list[Any], *, limit: int = CONTINUITY_CONTEXT_LIMIT) -> list[dict[str, Any]]:
    """Extract recent user emotion turns for continuity (no ML)."""
    ctx: list[dict[str, Any]] = []
    for msg in prior_messages:
        role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
        if role not in ("user",):
            continue
        if isinstance(msg, dict):
            emotion = msg.get("emotion")
            mental = msg.get("mental_state")
            conf = msg.get("emotion_confidence")
            content = msg.get("content") or msg.get("text") or ""
        else:
            emotion = getattr(msg, "emotion", None)
            mental = getattr(msg, "mental_state", None)
            conf = getattr(msg, "emotion_confidence", None)
            content = getattr(msg, "content", "") or ""
        if not emotion and not mental:
            continue
        ctx.append({
            "emotion": emotion,
            "mental_state": mental,
            "confidence": conf,
            "content": (content or "")[:220],
        })
    return ctx[-limit:]
