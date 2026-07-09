"""
Rule-based crisis escalation.

Runs after ML analysis and before response generation.
Overrides LOW/ MEDIUM ML crisis scores when high-risk phrases are detected.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Self-harm / immediate danger → CRISIS
CRISIS_PATTERNS: list[tuple[str, str]] = [
    (r"\bsuicid", "suicidal language"),
    (r"\bkill myself\b", "kill myself"),
    (r"\bend my life\b", "end my life"),
    (r"\bwant to die\b", "want to die"),
    (r"\bwish i was dead\b", "wish i was dead"),
    (r"\bself[- ]?harm\b", "self-harm"),
    (r"\bhurt myself\b", "hurt myself"),
    (r"\bcut myself\b", "cut myself"),
    (r"\boverdose\b", "overdose"),
    (r"\bno reason to live\b", "no reason to live"),
    (r"\bbetter off dead\b", "better off dead"),
    (r"\bend it all\b", "end it all"),
    (r"\btake my life\b", "take my life"),
]

# Severe hopelessness / giving up → HIGH (even when ML confidence is low)
HIGH_CRISIS_PHRASES: list[str] = [
    "i feel hopeless",
    "i'm hopeless",
    "im hopeless",
    "feeling hopeless",
    "feel hopeless",
    "i want to give up",
    "want to give up",
    "i'm giving up",
    "im giving up",
    "giving up on everything",
    "i can't do this anymore",
    "i cant do this anymore",
    "can't do this anymore",
    "cant do this anymore",
    "cannot do this anymore",
    "i can't go on",
    "i cant go on",
    "can't go on anymore",
    "cant go on anymore",
    "no point anymore",
    "what's the point",
    "whats the point",
    "i give up",
    "done with everything",
    "don't want to live",
    "dont want to live",
    "life isn't worth",
    "life isnt worth",
    "nothing matters anymore",
]


def check_rule_based_crisis(message: str) -> tuple[str | None, str | None]:
    """
    Return (risk_level, matched_signal) for rule-based escalation.
    risk_level is 'CRISIS' or 'HIGH', or (None, None) if no match.
    """
    text = message.strip().lower()
    if not text:
        return None, None

    for pattern, label in CRISIS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "CRISIS", label

    for phrase in HIGH_CRISIS_PHRASES:
        if phrase in text:
            return "HIGH", phrase

    return None, None


def apply_rule_based_crisis_override(message: str, analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Apply rule-based crisis escalation to ML analysis payload.
    Mutates crisis fields when a rule matches; preserves other analysis fields.
    """
    level, signal = check_rule_based_crisis(message)
    if not level:
        return analysis

    updated = dict(analysis)
    prev_risk = updated.get("crisis_risk", "LOW")
    prev_prob = float(updated.get("crisis_probability") or 0)

    updated["crisis_risk"] = level
    floor = 0.95 if level == "CRISIS" else 0.85
    updated["crisis_probability"] = max(prev_prob, floor)
    updated["requires_immediate_action"] = True
    updated["rule_crisis_override"] = signal

    logger.warning(
        "[Crisis] Rule-based escalation | signal=%r | %s → %s (ml was %s, p=%.2f)",
        signal,
        prev_risk,
        level,
        prev_risk,
        prev_prob,
    )
    return updated
