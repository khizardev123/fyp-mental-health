"""Unit tests for avatar-side emotion pipeline (Phase F-5)."""
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
        "confidence": 0.75,
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


def test_heartbreak_not_stable():
    a = _base("normal", "neutral", 1)
    a["all_scores"] = {"normal": 0.8, "joy": 0.1, "sadness": 0.1}
    a["confidence"] = 0.9
    r = finalize_emotion_analysis(
        "My girlfriend cheated on me and left me for someone else",
        a,
    )
    assert r["raw_label"] == "sadness"
    assert r["emotion"] == "sadness"
    assert r["mental_state"] != "Stable"
    assert any("heartbreak" in x for x in r.get("emotion_rules_applied", []))
    # Ranking must match refined label
    top = max(r["all_scores"].items(), key=lambda kv: kv[1])[0]
    assert top == "sadness"
    assert abs(r["confidence"] - r["all_scores"]["sadness"]) < 1e-6
    print("PASS heartbreak ->", r["raw_label"], r["mental_state"], "top=", top)


def test_grief_not_stable():
    a = _base("joy", "joy", 1)
    r = finalize_emotion_analysis("I've been grieving since my father passed away", a)
    assert r["raw_label"] == "grief"
    assert r["mental_state"] == "Grief"
    assert max(r["all_scores"], key=r["all_scores"].get) == "grief"
    print("PASS grief ->", r["raw_label"], r["mental_state"])


def test_burnout_not_stable():
    a = _base("normal", "neutral", 1)
    r = finalize_emotion_analysis("I'm burned out and emotionally exhausted from work", a)
    assert r["raw_label"] == "stress"
    assert r["emotion"] == "stress"
    print("PASS burnout ->", r["raw_label"], r["emotion"])


def test_panic_not_stable():
    a = _base("anger", "anger", 6)
    a["all_scores"] = {"anger": 0.7, "normal": 0.4, "anxiety": 0.2}
    r = finalize_emotion_analysis("My heart is racing and I can't breathe", a)
    assert r["raw_label"] == "anxiety"
    assert r["emotion"] == "anxiety"
    assert r["mental_state"] == "Acute Anxiety"
    assert r["raw_label"] != "anger"
    assert max(r["all_scores"], key=r["all_scores"].get) == "anxiety"
    assert r["all_scores"].get("anger", 0) < r["all_scores"]["anxiety"]
    print("PASS panic ->", r["raw_label"], r["mental_state"])


def test_loneliness_not_stable():
    a = _base("normal", "neutral", 1)
    r = finalize_emotion_analysis("I feel so lonely and isolated with no friends", a)
    assert r["raw_label"] == "sadness"
    assert r["mental_state"] != "Stable"
    print("PASS loneliness ->", r["raw_label"], r["mental_state"])


def test_followup_inherits_context():
    a = _base("normal", "neutral", 1)
    a["confidence"] = 0.85
    a["all_scores"] = {"normal": 0.9, "sadness": 0.05}
    ctx = [
        {
            "emotion": "sadness",
            "mental_state": "Sadness",
            "confidence": 0.8,
            "content": "My partner betrayed me and I feel heartbroken",
        }
    ]
    r = finalize_emotion_analysis("What are your thoughts?", a, conversation_context=ctx)
    assert r["raw_label"] == "sadness"
    assert r["emotion"] == "sadness"
    assert any("continuity" in x for x in r.get("emotion_rules_applied", []))
    assert max(r["all_scores"], key=r["all_scores"].get) == "sadness"
    print("PASS follow-up inherit ->", r["raw_label"], r["emotion_rules_applied"])


def test_memory_recall_neutral_after_stress_context():
    """Phase P0.5: recall questions must not inherit prior distress."""
    a = _base("normal", "neutral", 1)
    a["confidence"] = 0.48
    a["all_scores"] = {"normal": 0.58, "stress": 0.12, "joy": 0.08, "sadness": 0.1}
    ctx = [
        {
            "emotion": "stress",
            "mental_state": "Stress",
            "confidence": 0.75,
            "content": "I have three exams next week. I can't sleep. I'm mentally exhausted.",
        }
    ]
    recall_questions = [
        "What degree am I studying?",
        "What do you remember about me?",
        "What am I building?",
    ]
    for q in recall_questions:
        r = finalize_emotion_analysis(q, dict(a), conversation_context=ctx)
        assert not any("continuity_inherit" in x for x in r.get("emotion_rules_applied", [])), q
        assert r["raw_label"] == "normal", q
        assert r["emotion"] == "neutral", q
        assert r["mental_state"] == "Stable", q
        assert "academic pressure" not in r.get("tags", []), q
        print(f"PASS recall neutral -> {q[:40]!r} | {r['mental_state']} | tags={r.get('tags')}")


def test_recovery_allows_calm():
    a = _base("sadness", "sadness", 5)
    a["all_scores"] = {"sadness": 0.7, "normal": 0.2, "depression": 0.4}
    ctx = [
        {
            "emotion": "sadness",
            "mental_state": "Sadness",
            "confidence": 0.8,
            "content": "I was heartbroken yesterday",
        }
    ]
    r = finalize_emotion_analysis(
        "I talked with my family and now I feel much more relaxed",
        a,
        conversation_context=ctx,
    )
    assert r["raw_label"] in ("normal", "joy")
    assert not any("continuity_inherit" in x for x in r.get("emotion_rules_applied", []))
    assert any("recovery_override" in x for x in r.get("emotion_rules_applied", []))
    assert max(r["all_scores"], key=r["all_scores"].get) in ("normal", "joy")
    print("PASS recovery ->", r["raw_label"], r["emotion_rules_applied"])


def test_exam_stress_then_overwhelmed():
    """Escalation: exam stress context + 'I'm overwhelmed' must not classify as normal."""
    a = _base("normal", "neutral", 1)
    a["confidence"] = 0.82
    a["all_scores"] = {"normal": 0.85, "stress": 0.08, "anxiety": 0.05}
    ctx = [
        {
            "emotion": "stress",
            "mental_state": "Stress",
            "confidence": 0.72,
            "content": "I have exams. I'm stressed.",
        }
    ]
    r = finalize_emotion_analysis("I'm overwhelmed.", dict(a), conversation_context=ctx)
    assert r["raw_label"] in ("stress", "anxiety"), r
    assert r["emotion"] in ("stress", "anxiety"), r
    assert r["mental_state"] != "Stable"
    rules = r.get("emotion_rules_applied", [])
    assert any(
        "standalone_stress_kw" in x or "continuity_session_blend" in x or "continuity_inherit" in x
        for x in rules
    ), rules
    print("PASS exam->overwhelmed ->", r["raw_label"], rules)


def test_escalation_stress_to_anxiety_arc():
    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.7, "content": "Exams are killing me"},
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.68, "content": "Still so much to study"},
    ]
    a = _base("normal", "neutral", 1)
    a["confidence"] = 0.5
    a["all_scores"] = {"normal": 0.55, "stress": 0.2, "anxiety": 0.15}
    r = finalize_emotion_analysis("It's getting worse.", dict(a), conversation_context=ctx)
    assert r["raw_label"] in ("stress", "anxiety", "sadness")
    state = __import__("app.emotion_pipeline", fromlist=["compute_session_emotion_state"]).compute_session_emotion_state(ctx)
    assert state.trend in ("stable", "escalating")
    assert "Stress" in state.summary_line
    print("PASS escalation arc ->", r["raw_label"], state.summary_line.replace("\u2192", "->"))


def test_recovery_chain_stress_to_happy():
    """Stress → anxiety → recovery → happy should not stay locked in distress."""
    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.7, "content": "I have exams"},
        {"emotion": "anxiety", "mental_state": "Anxiety", "confidence": 0.65, "content": "I'm overwhelmed"},
    ]
    a = _base("normal", "neutral", 1)
    a["all_scores"] = {"normal": 0.6, "joy": 0.35, "stress": 0.1}
    r = finalize_emotion_analysis("I feel much better now. I'm happy!", dict(a), conversation_context=ctx)
    assert r["raw_label"] in ("normal", "joy"), r
    assert r["emotion"] in ("neutral", "joy"), r
    assert any("recovery_override" in x for x in r.get("emotion_rules_applied", []))
    print("PASS recovery chain ->", r["raw_label"], r.get("emotion_rules_applied"))


def test_crisis_overrides_session_stress():
    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.8, "content": "Exams are soon"},
    ]
    a = _base("normal", "neutral", 1)
    a["crisis_probability"] = 0.9
    a["all_scores"] = {"normal": 0.5, "crisis": 0.4}
    from app.crisis_rules import apply_rule_based_crisis_override

    r = finalize_emotion_analysis("I want to kill myself", dict(a), conversation_context=ctx)
    r = apply_rule_based_crisis_override("I want to kill myself", r)
    assert r.get("crisis_risk") in ("HIGH", "CRISIS") or r.get("rule_crisis_override")
    assert not any("continuity_session_blend" in x for x in r.get("emotion_rules_applied", []))
    print("PASS crisis override ->", r.get("crisis_risk"), r["raw_label"])


def test_trajectory_summary_for_prompt():
    from app.emotion_pipeline import build_emotion_trajectory_prompt_note, compute_session_emotion_state

    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.7, "content": "exams"},
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.68, "content": "still stressed"},
        {"emotion": "anxiety", "mental_state": "Anxiety", "confidence": 0.66, "content": "overwhelmed"},
    ]
    state = compute_session_emotion_state(ctx)
    assert state.summary_line == "Recent emotional journey: Stress → Stress → Anxiety"
    note = build_emotion_trajectory_prompt_note(state, {"emotion": "anxiety", "mental_state": "Anxiety"})
    assert note is not None
    assert "Recent emotional journey" in note
    assert "Stress → Stress → Anxiety" in note
    print("PASS trajectory prompt ->", state.summary_line.replace("\u2192", "->"))


def test_neutral_followup_inherits():
    a = _base("normal", "neutral", 1)
    a["confidence"] = 0.85
    ctx = [{"emotion": "stress", "mental_state": "Stress", "confidence": 0.75, "content": "Exams next week"}]
    r = finalize_emotion_analysis("Why?", dict(a), conversation_context=ctx)
    assert r["raw_label"] == "stress"
    assert any("continuity" in x for x in r.get("emotion_rules_applied", []))
    print("PASS neutral follow-up ->", r["raw_label"])


def test_joy_after_stress_session_not_blended():
    """P1: positive affect must override session distress continuity."""
    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.75, "content": "I'm so stressed."},
    ]
    a = _base("joy", "joy", 1)
    a["confidence"] = 0.72
    a["all_scores"] = {"joy": 0.72, "normal": 0.15, "stress": 0.1, "anxiety": 0.08}
    r = finalize_emotion_analysis(
        "Actually I just got an A on my project! I'm thrilled!",
        dict(a),
        conversation_context=ctx,
    )
    assert r["raw_label"] in ("joy", "normal"), r
    assert r["emotion"] in ("joy", "neutral"), r
    assert not any("continuity_session_blend" in x for x in r.get("emotion_rules_applied", []))
    assert any(
        x in " ".join(r.get("emotion_rules_applied", []))
        for x in ("positive_affect_priority", "current_message_priority")
    )
    print("PASS joy after stress ->", r["raw_label"], r.get("emotion_rules_applied"))


def test_hobby_joy_after_stress():
    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.75, "content": "I'm stressed about deadlines."},
    ]
    a = _base("joy", "joy", 1)
    a["confidence"] = 0.7
    a["all_scores"] = {"joy": 0.7, "normal": 0.2, "stress": 0.12}
    r = finalize_emotion_analysis(
        "I love cricket. Virat Kohli is my favourite.",
        dict(a),
        conversation_context=ctx,
    )
    assert r["raw_label"] in ("joy", "normal"), r
    assert r["emotion"] in ("joy", "neutral"), r
    assert not any("continuity_session_blend" in x for x in r.get("emotion_rules_applied", []))
    print("PASS hobby joy after stress ->", r["raw_label"])


def test_topic_shift_weather_after_heartbreak():
    ctx = [
        {
            "emotion": "sadness",
            "mental_state": "Sadness",
            "confidence": 0.8,
            "content": "I'm heartbroken after my breakup.",
        },
    ]
    a = _base("normal", "neutral", 1)
    a["confidence"] = 0.76
    r = finalize_emotion_analysis(
        "By the way, what's the weather like for hiking?",
        dict(a),
        conversation_context=ctx,
    )
    assert r["raw_label"] == "normal", r
    assert r["emotion"] == "neutral", r
    assert any("topic_shift_skip" in x for x in r.get("emotion_rules_applied", []))
    assert not any("continuity_inherit" in x for x in r.get("emotion_rules_applied", []))
    print("PASS topic shift weather ->", r["raw_label"], r.get("emotion_rules_applied"))


def test_partial_recovery_bit_better():
    ctx = [
        {"emotion": "anxiety", "mental_state": "Anxiety", "confidence": 0.7, "content": "I'm overwhelmed."},
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.68, "content": "Exams are soon."},
    ]
    a = _base("anxiety", "anxiety", 5)
    a["confidence"] = 0.55
    a["all_scores"] = {"anxiety": 0.55, "stress": 0.3, "normal": 0.25, "joy": 0.1}
    r = finalize_emotion_analysis(
        "I talked to my friend and feel a bit better.",
        dict(a),
        conversation_context=ctx,
    )
    assert r["raw_label"] in ("stress", "normal"), r
    assert r["raw_label"] != "anxiety", r
    assert any("partial_recovery" in x for x in r.get("emotion_rules_applied", []))
    print("PASS partial recovery ->", r["raw_label"], r.get("emotion_rules_applied"))


def test_mild_escalation_cap_cant_focus():
    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.72, "content": "Exams are soon."},
    ]
    a = _base("fear", "fear", 6)
    a["confidence"] = 0.68
    a["all_scores"] = {"fear": 0.68, "anxiety": 0.45, "stress": 0.3, "normal": 0.1}
    r = finalize_emotion_analysis("I can't focus at all.", dict(a), conversation_context=ctx)
    assert r["raw_label"] in ("stress", "anxiety"), r
    assert r["raw_label"] != "fear", r
    print("PASS mild escalation cap can't focus ->", r["raw_label"], r.get("emotion_rules_applied"))


def test_mild_escalation_getting_harder():
    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.7, "content": "School has been a lot."},
        {"emotion": "anxiety", "mental_state": "Anxiety", "confidence": 0.65, "content": "I'm worried."},
    ]
    a = _base("fear", "fear", 6)
    a["confidence"] = 0.62
    a["all_scores"] = {"fear": 0.62, "anxiety": 0.5, "stress": 0.35}
    r = finalize_emotion_analysis("It's getting harder.", dict(a), conversation_context=ctx)
    assert r["raw_label"] in ("stress", "anxiety"), r
    assert r["raw_label"] != "fear", r
    print("PASS mild escalation getting harder ->", r["raw_label"], r.get("emotion_rules_applied"))


def test_trajectory_prompt_recovery_emphasis():
    from app.emotion_pipeline import build_emotion_trajectory_prompt_note, compute_session_emotion_state

    ctx = [
        {"emotion": "stress", "mental_state": "Stress", "confidence": 0.7, "content": "exams"},
        {"emotion": "anxiety", "mental_state": "Anxiety", "confidence": 0.68, "content": "overwhelmed"},
    ]
    state = compute_session_emotion_state(ctx)
    analysis = {
        "mental_state": "Stable",
        "emotion": "neutral",
        "raw_label": "normal",
        "emotion_rules_applied": ["partial_recovery->stress"],
    }
    note = build_emotion_trajectory_prompt_note(state, analysis)
    assert note is not None
    assert "Current direction" in note
    assert "recovery" in note.lower()
    assert "Prior context (background only)" in note
    assert "stale session distress" in note.lower() or "Do not carry forward stale session distress" in note
    print("PASS trajectory recovery prompt ->", note[:120], "...")


def test_score_ranking_matches_refined_label():
    a = _base("normal", "neutral", 1)
    a["all_scores"] = {
        "normal": 0.78,
        "sadness": 0.62,
        "depression": 0.45,
        "joy": 0.1,
        "anxiety": 0.2,
    }
    a["confidence"] = 0.78
    r = finalize_emotion_analysis(
        "I feel heartbroken after the betrayal",
        a,
    )
    assert r["raw_label"] == "sadness"
    assert r["mental_state"] == "Sadness"
    top_cls, top_prob = max(r["all_scores"].items(), key=lambda kv: kv[1])
    assert top_cls == "sadness"
    assert top_prob >= r["all_scores"]["normal"]
    assert abs(r["confidence"] - top_prob) < 1e-6
    print("PASS ranking sync ->", top_cls, f"{top_prob:.2f}", "conf", r["confidence"])


def test_weighted_dominant_prefers_intensity():
    # Significant betrayal should outweigh calm follow-ups
    intensity = {
        "sad": 7.2, "calm": 1.0, "anxious": 7.4, "stressed": 6.2, "happy": 1.5, "grief": 9.0,
    }
    importance = {"sad": 1.45, "calm": 0.5, "anxious": 1.4, "stressed": 1.35, "happy": 0.7, "grief": 1.7}
    friendly = {
        "sadness": "sad", "neutral": "calm", "anxiety": "anxious",
        "stress": "stressed", "joy": "happy", "grief": "grief",
    }

    timeline = [
        {"emotion": "joy", "confidence": 0.7, "mental_state": "Joy", "content": "I felt happy this morning"},
        {
            "emotion": "sadness",
            "confidence": 0.85,
            "mental_state": "Sadness",
            "content": "My girlfriend cheated on me and left me",
        },
        {"emotion": "neutral", "confidence": 0.6, "mental_state": "Stable", "content": "What are your thoughts?"},
        {"emotion": "neutral", "confidence": 0.55, "mental_state": "Stable", "content": "Can you help me?"},
        {"emotion": "neutral", "confidence": 0.5, "mental_state": "Stable", "content": "Why?"},
    ]
    significant = ("cheated", "betrayal", "heartbreak", "passed away", "lost my")
    followup = ("what are your thoughts", "can you help", "why")

    def content_mult(c: str) -> float:
        t = c.lower()
        if any(k in t for k in significant):
            return 1.55
        if any(k in t for k in followup) or (len(t.split()) <= 8 and t.endswith("?")):
            return 0.35
        return 1.0

    normalized = [friendly.get(t["emotion"], t["emotion"]) for t in timeline]
    n = len(normalized)
    scores: dict[str, float] = {}
    for i, emo in enumerate(normalized):
        conf_f = float(timeline[i]["confidence"])
        recency = 0.35 + 0.65 * (i / max(n - 1, 1))
        mult = content_mult(timeline[i]["content"])
        weight = (
            intensity.get(emo, 3)
            * (0.45 + 0.55 * conf_f)
            * recency
            * importance.get(emo, 1.0)
            * mult
        )
        scores[emo] = scores.get(emo, 0.0) + weight
    dominant = max(scores.items(), key=lambda kv: kv[1])[0]
    assert dominant == "sad"
    print("PASS weighted dominant ->", dominant, scores)


if __name__ == "__main__":
    test_negated_happy()
    test_exam_stress()
    test_failure()
    test_heartbreak_not_stable()
    test_grief_not_stable()
    test_burnout_not_stable()
    test_panic_not_stable()
    test_loneliness_not_stable()
    test_followup_inherits_context()
    test_memory_recall_neutral_after_stress_context()
    test_recovery_allows_calm()
    test_exam_stress_then_overwhelmed()
    test_escalation_stress_to_anxiety_arc()
    test_recovery_chain_stress_to_happy()
    test_crisis_overrides_session_stress()
    test_trajectory_summary_for_prompt()
    test_neutral_followup_inherits()
    test_joy_after_stress_session_not_blended()
    test_hobby_joy_after_stress()
    test_topic_shift_weather_after_heartbreak()
    test_partial_recovery_bit_better()
    test_mild_escalation_cap_cant_focus()
    test_mild_escalation_getting_harder()
    test_trajectory_prompt_recovery_emphasis()
    test_score_ranking_matches_refined_label()
    test_weighted_dominant_prefers_intensity()
    print("All avatar emotion pipeline tests passed")
