"""Verify emotion pipeline synchronization for example messages."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.emotion_pipeline import finalize_emotion_analysis

CASES = [
    {
        "message": "I feel stressed because of my exams",
        "ml": {
            "raw_label": "depression",
            "emotion": "sadness",
            "mental_state": "Depression",
            "severity_rating": 8,
            "confidence": 0.62,
            "all_scores": {"depression": 0.62, "stress": 0.4, "anxiety": 0.35, "joy": 0.05},
            "crisis_probability": 0.05,
            "semantic_summary": "Text reflects depressive patterns...",
        },
        "expect_label": ("stress", "anxiety"),
        "expect_emotion": ("stress", "anxiety"),
        "expect_mental": ("Stress", "Anxiety"),
        "max_severity": 6,
    },
    {
        "message": "I failed one subject last semester",
        "ml": {
            "raw_label": "normal",
            "emotion": "neutral",
            "mental_state": "Stable",
            "severity_rating": 1,
            "confidence": 0.55,
            "all_scores": {"normal": 0.55, "stress": 0.2, "depression": 0.15},
            "crisis_probability": 0.02,
            "semantic_summary": "Text appears emotionally stable...",
        },
        "expect_label": ("stress",),
        "expect_emotion": ("stress",),
        "expect_mental": ("Stress",),
        "max_severity": 6,
    },
    {
        "message": "I am not happy today",
        "ml": {
            "raw_label": "joy",
            "emotion": "joy",
            "mental_state": "Joy",
            "severity_rating": 1,
            "confidence": 0.7,
            "all_scores": {"joy": 0.7, "stress": 0.1, "depression": 0.1},
            "crisis_probability": 0.01,
            "semantic_summary": "Positive emotional state...",
        },
        "expect_label": ("sadness",),
        "expect_emotion": ("sadness",),
        "expect_mental": ("Sadness",),
        "max_severity": 5,
    },
    {
        "message": "Just exam pressure",
        "ml": {
            "raw_label": "normal",
            "emotion": "neutral",
            "mental_state": "Stable",
            "severity_rating": 1,
            "confidence": 0.6,
            "all_scores": {"normal": 0.6, "stress": 0.2},
            "crisis_probability": 0.02,
            "semantic_summary": "Stable...",
        },
        "expect_label": ("stress",),
        "expect_emotion": ("stress",),
        "expect_mental": ("Stress",),
        "max_severity": 6,
        "expect_tag": "academic pressure",
    },
    {
        "message": "My exams are next week",
        "ml": {
            "raw_label": "normal",
            "emotion": "neutral",
            "mental_state": "Stable",
            "severity_rating": 1,
            "confidence": 0.58,
            "all_scores": {"normal": 0.58, "anxiety": 0.25},
            "crisis_probability": 0.02,
            "semantic_summary": "Stable...",
        },
        "expect_label": ("stress", "anxiety"),
        "expect_emotion": ("stress", "anxiety"),
        "expect_mental": ("Stress", "Anxiety"),
        "max_severity": 6,
        "expect_tag": "academic pressure",
    },
]


def run() -> int:
    print("=" * 60)
    print("Emotion Pipeline Sync Verification")
    print("=" * 60)
    passed = 0
    for case in CASES:
        msg = case["message"]
        ml = dict(case["ml"])
        ml["ml_raw_label"] = ml["raw_label"]
        result = finalize_emotion_analysis(msg, ml)

        ok = True
        if result["raw_label"] not in case["expect_label"]:
            ok = False
        if result["emotion"] not in case["expect_emotion"]:
            ok = False
        if result["mental_state"] not in case["expect_mental"]:
            ok = False
        if result["severity_rating"] > case["max_severity"]:
            ok = False
        if result["emotion"] != result.get("final_emotion"):
            ok = False
        if result["mental_state"] != result.get("final_mental_state"):
            ok = False
        if "depressive patterns" in result["semantic_summary"].lower() and result["raw_label"] in ("stress", "anxiety"):
            ok = False
        if case.get("expect_tag") and case["expect_tag"] not in result.get("tags", []):
            ok = False
        if result.get("semantic_summary") and result["raw_label"] in ("stress", "anxiety"):
            if "depressive" in result["semantic_summary"].lower():
                ok = False

        status = "PASS" if ok else "FAIL"
        print(f"\n{status}: {msg}")
        print(f"  Raw ML        -> {ml['raw_label']} ({ml['confidence']})")
        print(f"  Rules         -> {result.get('emotion_rules_applied', [])}")
        print(f"  Final label   -> {result['raw_label']}")
        print(f"  Emotion       -> {result['emotion']}")
        print(f"  Mental State  -> {result['mental_state']}")
        print(f"  Severity      -> {result['severity_rating']}")
        print(f"  Assessment    -> {result['semantic_summary'][:90]}...")
        print(f"  Avatar hint   -> {result.get('avatar_emotion_hint')}")
        if ok:
            passed += 1

    print(f"\n{passed}/{len(CASES)} passed")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(run())
