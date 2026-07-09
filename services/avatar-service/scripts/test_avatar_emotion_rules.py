"""Unit tests for avatar-side emotion pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.emotion_pipeline import finalize_emotion_analysis


def _base(label="joy", emotion="joy", severity=1):
    return {
        "raw_label": label,
        "ml_raw_label": label,
        "emotion": emotion,
        "mental_state": "Joy",
        "severity_rating": severity,
        "all_scores": {"joy": 0.7, "stress": 0.2, "depression": 0.3, "anxiety": 0.25},
        "crisis_probability": 0.02,
    }


def test_negated_happy():
    r = finalize_emotion_analysis("I am not happy right now", _base())
    assert r["emotion"] == "sadness"
    assert r["raw_label"] == "sadness"
    print("PASS negated happy ->", r["raw_label"], r["emotion"])


def test_exam_stress():
    a = _base("depression", "sadness", 8)
    a["all_scores"] = {"depression": 0.6, "stress": 0.4, "anxiety": 0.35, "joy": 0.05}
    r = finalize_emotion_analysis("I feel stressed because of my exams", a)
    assert r["raw_label"] in ("stress", "anxiety")
    assert r["emotion"] in ("stress", "anxiety")
    assert r["mental_state"] in ("Stress", "Anxiety")
    assert r["severity_rating"] <= 6
    assert "depressive" not in r["semantic_summary"].lower()
    print("PASS exam stress ->", r["raw_label"], r["emotion"], r["severity_rating"])


def test_failure():
    a = _base("normal", "neutral", 1)
    a["all_scores"] = {"normal": 0.55, "depression": 0.2, "stress": 0.25}
    r = finalize_emotion_analysis("I failed one subject last semester", a)
    assert r["raw_label"] == "stress"
    assert r["emotion"] == "stress"
    assert r["mental_state"] == "Stress"
    assert r["severity_rating"] <= 6
    assert r["severity_rating"] >= 4
    print("PASS failure ->", r["raw_label"], r["emotion"], r["severity_rating"])


if __name__ == "__main__":
    test_negated_happy()
    test_exam_stress()
    test_failure()
    print("All avatar emotion pipeline tests passed")
