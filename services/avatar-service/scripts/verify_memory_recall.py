#!/usr/bin/env python3
"""Verify factual + preference + emotional memory retrieval and prompt construction."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.intent_gate import detect_intent
from app.prompt_builder import build_prompt_messages
from app.services.memory_retrieval import (
    classify_memory_type,
    is_memory_recall_query,
    retrieve_memories_for_prompt,
    session_user_memories,
)


class _Msg:
    def __init__(self, content: str, mid: str, ts: str = "2026-01-01T12:00:00+00:00"):
        self.id = mid
        self.session_id = "sess-demo"
        self.role = "user"
        self.content = content
        self.emotion = None
        from datetime import datetime, timezone
        self.timestamp = datetime.fromisoformat(ts)


def check(name: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    print("=" * 60)
    print("Memory Retrieval Verification")
    print("=" * 60)
    passed = 0
    total = 0

    seeds = [
        "My name is Muhammad Khizar",
        "I love football.",
        "Brazil is my favourite team.",
        "Messi is my favourite player.",
        "I failed my exam last semester",
    ]
    messages = [_Msg(t, f"m{i}") for i, t in enumerate(seeds)]

    types = {t: classify_memory_type(t) for t in seeds}
    total += 1
    if check("Name classified factual", types[seeds[0]] == "factual", types[seeds[0]]):
        passed += 1
    total += 1
    if check("Football classified preference", types[seeds[1]] == "preference", types[seeds[1]]):
        passed += 1
    total += 1
    if check("Brazil classified preference", types[seeds[2]] == "preference", types[seeds[2]]):
        passed += 1
    total += 1
    if check("Messi classified preference", types[seeds[3]] == "preference", types[seeds[3]]):
        passed += 1
    total += 1
    if check("Exam failure classified emotional", types[seeds[4]] == "emotional", types[seeds[4]]):
        passed += 1

    recall_q = "What do you remember about me?"
    total += 1
    if check("Recall query detected", is_memory_recall_query(recall_q)):
        passed += 1
    total += 1
    if check("Recall intent", detect_intent(recall_q) == "memory_recall"):
        passed += 1

    session_mems = session_user_memories(messages)
    total += 1
    if check("Session stores all 5 turns", len(session_mems) == 5, str(len(session_mems))):
        passed += 1

    # Simulate live bug: chat HISTORY_WINDOW truncates prior_messages but not session_user_messages
    truncated_prior = messages[-2:]  # only last 2 user msgs visible in chat window
    full_recall = retrieve_memories_for_prompt(
        user_id="demo-user",
        query=recall_q,
        session_id="sess-demo",
        session_user_messages=messages,
    )
    truncated_recall = retrieve_memories_for_prompt(
        user_id="demo-user",
        query=recall_q,
        session_id="sess-demo",
        session_user_messages=truncated_prior,
    )
    full_text = " ".join((m.get("text") or "").lower() for m in full_recall)
    total += 1
    if check("Full session recall includes name", "khizar" in full_text):
        passed += 1

    recalled = full_recall
    recalled_text = " ".join((m.get("text") or "").lower() for m in recalled)
    for needle in ("muhammad", "khizar", "football", "brazil", "messi"):
        total += 1
        if check(f"Recall includes '{needle}'", needle in recalled_text):
            passed += 1

    prompt = build_prompt_messages(
        current_message=recall_q,
        history=[],
        analysis={
            "emotion": "neutral",
            "mental_state": "Stable",
            "severity_rating": 2,
            "semantic_summary": "Recall request.",
            "tags": ["stable"],
            "crisis_risk": "LOW",
        },
        intent="memory_recall",
        relevant_memories=recalled,
    )
    user_block = prompt[-1]["content"]
    total += 1
    if check("Prompt has About the user section", "About the user" in user_block):
        passed += 1
    total += 1
    if check("Prompt has Preferences section", "Preferences" in user_block):
        passed += 1
    total += 1
    if check("Prompt forbids invention", "do not invent" in user_block.lower()):
        passed += 1

    print(f"\nResult: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
