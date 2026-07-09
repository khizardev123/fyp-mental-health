"""Unit tests for emotion context rules."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ai-service"))

from app.models.emotion_context_rules import apply_emotion_context_rules


def test_negated_happy():
    label, scores, conf, meta = apply_emotion_context_rules(
        "I am not happy right now", "joy", {"joy": 0.7, "stress": 0.2, "depression": 0.3}, 0.7
    )
    assert label != "joy", f"expected not joy, got {label}"
    print("PASS negated happy ->", label, meta)


def test_exam_stress():
    label, scores, conf, meta = apply_emotion_context_rules(
        "I feel stressed about my exams",
        "depression",
        {"depression": 0.6, "stress": 0.4, "anxiety": 0.35},
        0.6,
    )
    assert label in ("stress", "anxiety"), f"expected stress/anxiety, got {label}"
    print("PASS exam stress ->", label, meta)


def test_academic_failure():
    label, scores, conf, meta = apply_emotion_context_rules(
        "I failed my exam last semester",
        "depression",
        {"depression": 0.65, "stress": 0.3},
        0.65,
    )
    assert label == "stress", f"expected stress, got {label}"
    assert meta.get("severity_cap") == 6
    print("PASS academic failure ->", label, meta)


if __name__ == "__main__":
    test_negated_happy()
    test_exam_stress()
    test_academic_failure()
    print("All emotion rule tests passed")
