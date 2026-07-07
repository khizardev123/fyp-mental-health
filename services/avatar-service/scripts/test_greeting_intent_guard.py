"""Regression tests: greetings/self-intros must not be forced to crisis on ML HIGH."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crisis_rules import check_rule_based_crisis
from app.intent_gate import detect_intent
from app.prompt_builder import FRESH_INTENTS


def _resolve_intent_like_chat_service(message: str, crisis_risk: str) -> str:
    """Mirror chat_service intent resolution after ML (no DB)."""
    intent = detect_intent(message, ml_crisis_level=crisis_risk)
    rule_level, _ = check_rule_based_crisis(message)
    if rule_level:
        return "crisis"
    if crisis_risk in ("HIGH", "CRISIS") and intent not in FRESH_INTENTS:
        return "crisis"
    return intent


def test_self_intro_stays_greeting_on_ml_high() -> None:
    for msg in (
        "Hi, I am Khizar",
        "Hello, I'm John",
        "Hi there, I am Sarah",
    ):
        intent = _resolve_intent_like_chat_service(msg, "HIGH")
        assert intent == "greeting", f"{msg!r} → {intent}"


def test_plain_greetings_unchanged() -> None:
    for msg in ("Hello", "Hi there"):
        intent = _resolve_intent_like_chat_service(msg, "LOW")
        assert intent == "greeting", f"{msg!r} → {intent}"


def test_explicit_crisis_still_crisis() -> None:
    msg = "I want to end my life"
    intent = _resolve_intent_like_chat_service(msg, "CRISIS")
    assert intent == "crisis"


def test_rule_based_crisis_still_wins_over_greeting_prefix() -> None:
    # Greeting word present but explicit crisis phrase must still escalate
    msg = "Hi, I want to end my life"
    intent = _resolve_intent_like_chat_service(msg, "LOW")
    assert intent == "crisis"


if __name__ == "__main__":
    test_self_intro_stays_greeting_on_ml_high()
    test_plain_greetings_unchanged()
    test_explicit_crisis_still_crisis()
    test_rule_based_crisis_still_wins_over_greeting_prefix()
    print("All greeting intent guard tests passed.")
