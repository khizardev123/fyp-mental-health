"""Tests for prompt-layer improvements (personality, crisis, memory, turn guidance)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.prompt_builder import (
    SERENEMIND_PERSONALITY,
    build_crisis_context_note,
    build_prompt_messages,
    build_turn_guidance_note,
    infer_crisis_profile,
    infer_turn_mode,
    _format_memories_conversational,
    fallback_reply,
)


def test_personality_in_all_conversational_intents():
    for intent in ("greeting", "small_talk", "emotional_share", "factual", "memory_recall"):
        msgs = build_prompt_messages(
            current_message="Hello" if intent != "memory_recall" else "What do you remember?",
            history=[],
            analysis={"crisis_risk": "LOW", "emotion": "neutral", "severity_rating": 1, "tags": []},
            intent=intent,
            relevant_memories=[{"text": "I love cricket"}] if intent == "memory_recall" else [],
        )
        system = msgs[0]["content"]
        assert "2-4 short sentences" in system or SERENEMIND_PERSONALITY[:40] in system
        assert "observe" in system.lower()
    print("PASS personality core in all intents")


def test_greeting_inherits_personality():
    msgs = build_prompt_messages(
        current_message="Hey!",
        history=[],
        analysis={"crisis_risk": "LOW"},
        intent="greeting",
    )
    assert "thoughtful friend" in msgs[0]["content"].lower()
    print("PASS greeting inherits personality")


def test_crisis_situation_profiles():
    assert infer_crisis_profile("I want to kill myself", {"crisis_risk": "CRISIS"}) == "suicidal_ideation"
    assert infer_crisis_profile("I feel hopeless", {"crisis_risk": "HIGH"}) == "hopelessness"
    assert infer_crisis_profile("I'm having a panic attack", {"crisis_risk": "HIGH"}) == "panic"
    assert infer_crisis_profile("My father passed away", {"crisis_risk": "LOW", "tags": ["loss"]}) == "grief"
    assert infer_crisis_profile("I feel so lonely", {"crisis_risk": "LOW", "tags": ["loneliness"]}) == "loneliness"
    print("PASS crisis profiles")


def test_crisis_prompt_has_helpline_and_no_clinical_block():
    msgs = build_prompt_messages(
        current_message="I feel hopeless about everything",
        history=[],
        analysis={
            "crisis_risk": "HIGH",
            "emotion": "sadness",
            "mental_state": "Sadness",
            "severity_rating": 4,
            "tags": ["hopelessness"],
        },
        intent="crisis",
    )
    system = msgs[0]["content"]
    user = msgs[-1]["content"]
    assert "0317-4288665" in system
    assert "exactly ONE" in system or "one gentle safety question" in system.lower()
    assert "Current analysis:" not in user
    assert "hopelessness" in user.lower() or "Profile:" in user
    print("PASS crisis prompt structure")


def test_crisis_fallback_situation_aware():
    fb = fallback_reply("crisis", {"crisis_risk": "CRISIS"}, "I want to kill myself")
    assert "0317-4288665" in fb
    assert "?" in fb
    fb2 = fallback_reply("crisis", {"crisis_risk": "HIGH"}, "I feel so lonely")
    assert "0317-4288665" in fb2
    assert "?" in fb2
    print("PASS crisis fallback")


def test_memory_conversational_max_two():
    mems = [
        {"text": "My name is Khizar"},
        {"text": "I love cricket"},
        {"text": "I study CS"},
        {"text": "Brazil is my team"},
    ]
    out = _format_memories_conversational(mems)
    assert out.count("\n") + 1 <= 2 if out else True
    assert "About the user" not in out
    assert "Preferences:" not in out
    assert out.startswith("- ")
    print("PASS memory conversational format")


def test_memory_skips_recently_surfaced():
    mems = [{"text": "I love cricket and Virat Kohli"}]
    history = [{"role": "assistant", "content": "You love cricket and Virat Kohli — nice."}]
    out = _format_memories_conversational(mems, history)
    assert out == ""
    print("PASS memory anti-repeat")


def test_turn_mode_no_consecutive_ask():
    history = [{"role": "assistant", "content": "What's weighing on you most?"}]
    mode = infer_turn_mode(
        intent="emotional_share",
        analysis={"emotion": "stress", "tags": []},
        history=history,
        message="Exams are next week and I'm stressed.",
    )
    assert mode in ("listen", "reflect", "support")
    assert mode != "ask"
    note = build_turn_guidance_note(mode)
    assert "ask" not in note.lower() or "no question" in note.lower()
    print("PASS no consecutive ask")


def test_turn_guidance_in_emotional_prompt():
    msgs = build_prompt_messages(
        current_message="I'm stressed about exams",
        history=[],
        analysis={"crisis_risk": "LOW", "emotion": "stress", "severity_rating": 5, "tags": ["pressure"]},
        intent="emotional_share",
    )
    user = msgs[-1]["content"]
    assert "Conversation guidance" in user
    assert "Current analysis:" not in user
    assert "Tone guidance" in user
    print("PASS turn guidance + tone note")


def test_memory_recall_no_category_dump():
    msgs = build_prompt_messages(
        current_message="What do you remember about me?",
        history=[],
        analysis={"crisis_risk": "LOW", "emotion": "neutral", "mental_state": "Stable", "severity_rating": 1, "tags": []},
        intent="memory_recall",
        relevant_memories=[
            {"text": "My name is Khizar", "memory_type": "factual"},
            {"text": "I love cricket", "memory_type": "preference"},
        ],
    )
    user = msgs[-1]["content"]
    assert "About the user" not in user
    assert "never invent" in user.lower()
    assert "Khizar" in user or "cricket" in user
    print("PASS recall conversational")


if __name__ == "__main__":
    test_personality_in_all_conversational_intents()
    test_greeting_inherits_personality()
    test_crisis_situation_profiles()
    test_crisis_prompt_has_helpline_and_no_clinical_block()
    test_crisis_fallback_situation_aware()
    test_memory_conversational_max_two()
    test_memory_skips_recently_surfaced()
    test_turn_mode_no_consecutive_ask()
    test_turn_guidance_in_emotional_prompt()
    test_memory_recall_no_category_dump()
    print("All prompt improvement tests passed")
