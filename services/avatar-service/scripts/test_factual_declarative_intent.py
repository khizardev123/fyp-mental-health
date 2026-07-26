"""Regression tests: Phase P0.5-B neutral declarative routing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.intent_gate import detect_intent


SERENEMIND_DESC = (
    "SereneMind focuses on providing personalized, emotionally intelligent mental "
    "wellness support through AI-driven conversations."
)


def test_neutral_declaratives_route_to_factual() -> None:
    cases = [
        SERENEMIND_DESC,
        "I am a Computer Science student.",
        "My Final Year Project is called SereneMind.",
        "I love cricket. Virat Kohli is my favourite batsman.",
    ]
    for msg in cases:
        intent = detect_intent(msg)
        assert intent == "factual", f"{msg[:60]!r} → {intent}, expected factual"


def test_distress_still_routes_to_emotional_share() -> None:
    cases = [
        "I've been mentally exhausted because of exams.",
        "I'm building SereneMind but honestly I'm overwhelmed.",
        "I have exams. I'm stressed.",
    ]
    for msg in cases:
        intent = detect_intent(msg)
        assert intent == "emotional_share", f"{msg!r} → {intent}, expected emotional_share"


def test_greeting_crisis_recall_unchanged() -> None:
    assert detect_intent("Hi, my name is Khizar.") == "greeting"
    assert detect_intent("I want to end my life") == "crisis"
    assert detect_intent("What degree am I studying?") == "memory_recall"


if __name__ == "__main__":
    test_neutral_declaratives_route_to_factual()
    test_distress_still_routes_to_emotional_share()
    test_greeting_crisis_recall_unchanged()
    print("All factual declarative intent tests passed.")
