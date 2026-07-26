"""Unit tests for crisis rules and prompt memory guidance."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crisis_rules import apply_rule_based_crisis_override, check_rule_based_crisis
from app.prompt_builder import build_prompt_messages


def test_high_crisis_phrases() -> None:
    cases = [
        ("I feel hopeless about everything", "HIGH"),
        ("I want to give up", "HIGH"),
        ("I can't do this anymore", "HIGH"),
        ("I cant do this anymore", "HIGH"),
    ]
    for msg, expected in cases:
        level, signal = check_rule_based_crisis(msg)
        assert level == expected, f"{msg!r} → {level} (expected {expected}), signal={signal}"


def test_crisis_override_low_ml() -> None:
    analysis = {"crisis_risk": "LOW", "crisis_probability": 0.1, "emotion": "neutral"}
    updated = apply_rule_based_crisis_override("I feel hopeless", analysis)
    assert updated["crisis_risk"] == "HIGH"
    assert updated["crisis_probability"] >= 0.85
    assert updated.get("rule_crisis_override")


def test_no_false_positive_greeting() -> None:
    level, _ = check_rule_based_crisis("Hi there!")
    assert level is None


def test_memory_prompt_no_assume_again() -> None:
    msgs = build_prompt_messages(
        current_message="Hello",
        history=[],
        analysis={"crisis_risk": "LOW", "crisis_probability": 0.0},
        intent="greeting",
        relevant_memories=[],
    )
    assert msgs[-1]["content"] == "Hello"
    assert "fresh" in msgs[0]["content"].lower() or "greeting" in msgs[0]["content"].lower()


def test_memory_prompt_includes_memories() -> None:
    msgs = build_prompt_messages(
        current_message="My exams are next week",
        history=[],
        analysis={"crisis_risk": "LOW"},
        intent="emotional_share",
        relevant_memories=[{"text": "I failed an exam last semester", "score": 0.92}],
    )
    content = msgs[-1]["content"]
    assert "failed an exam" in content
    assert "Verified memories" in content
    assert "About the user" not in content


if __name__ == "__main__":
    test_high_crisis_phrases()
    test_crisis_override_low_ml()
    test_no_false_positive_greeting()
    test_memory_prompt_no_assume_again()
    test_memory_prompt_includes_memories()
    print("All crisis/prompt tests passed.")
