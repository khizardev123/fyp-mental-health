#!/usr/bin/env python3
"""End-to-end FYP demo verification — pipeline stages without new features."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.emotion_pipeline import finalize_emotion_analysis
from app.prompt_builder import build_prompt_messages
from app.services.emotion_fusion import build_fusion_prompt_context, fuse_emotions
from app.chat_repository import build_analysis_payload, session_context_memories


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def check(name: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    line = f"  [{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


async def main() -> int:
    passed = 0
    total = 0

    section("1. Unified emotion object (text ML + rules)")
    cases = [
        ("I failed my exam", "stress"),
        ("I am not happy today", "sadness"),
        ("Hello", "normal"),
    ]
    for msg, expected_label_fragment in cases:
        raw = {
            "unified": {
                "raw_label": "normal",
                "emotion": "neutral",
                "mental_state": "Normal",
                "confidence": 0.7,
                "all_scores": {"normal": 0.7},
                "crisis_risk": "LOW",
                "crisis_probability": 0.05,
                "severity_rating": 2,
                "tags": [],
            }
        }
        if "not happy" in msg:
            raw["unified"]["raw_label"] = "joy"
            raw["unified"]["emotion"] = "joy"
            expected_label_fragment = "sadness"
        analysis = build_analysis_payload(raw)
        analysis = finalize_emotion_analysis(msg, analysis)
        ok = (
            analysis["emotion"] == analysis["final_emotion"]
            and analysis["mental_state"] == analysis["final_mental_state"]
            and expected_label_fragment in (analysis["raw_label"], analysis["emotion"])
        )
        total += 1
        if check(f'"{msg[:30]}"', ok, f"emotion={analysis['emotion']} mental={analysis['mental_state']}"):
            passed += 1

    section("2. Face + text fusion -> LLM prompt")
    fusion = fuse_emotions("neutral", "sad", 0.65)
    note = build_fusion_prompt_context(
        message="I'm fine.",
        text_emotion="neutral",
        face_emotion="sad",
        face_confidence=0.65,
        fusion=fusion,
    )
    total += 1
    if check("Fusion active for high face confidence", fusion["fusion_active"]):
        passed += 1
    total += 1
    if check("Fusion note mentions mismatch", note is not None and "sad" in note.lower()):
        passed += 1

    low = fuse_emotions("sadness", "happy", 0.1)
    total += 1
    if check("Low face confidence -> text only", not low["fusion_active"]):
        passed += 1

    section("3. RAG memories in prompt")
    memories = [{"text": "I failed my exam last week", "score": 0.88}]
    analysis = {"emotion": "stress", "mental_state": "Stress", "severity_rating": 6, "crisis_risk": "LOW"}
    msgs = build_prompt_messages(
        current_message="Exams are coming again and I feel overwhelmed",
        history=[{"role": "user", "content": "Hi"}],
        analysis=analysis,
        intent="emotional_share",
        relevant_memories=memories,
        fusion_note=None,
    )
    user_block = msgs[-1]["content"]
    total += 1
    if check("Memories embedded in user prompt", "Verified past memories" in user_block):
        passed += 1
    total += 1
    if check("Analysis block present", "emotion=stress" in user_block):
        passed += 1

    section("4. Session DB memory fallback")
    class _Msg:
        def __init__(self, content: str, mid: str = "m1"):
            self.id = mid
            self.session_id = "sess-1"
            self.role = "user"
            self.content = content
            self.emotion = "stress"

    db_mems = session_context_memories([_Msg("Earlier I said exams stress me out")])
    total += 1
    if check("Session fallback produces memories", len(db_mems) == 1):
        passed += 1

    section("5. Pipeline summary")
    print(
        json.dumps(
            {
                "stages": [
                    "Text -> ML (ai-service)",
                    "ML -> finalize_emotion_analysis (unified fields)",
                    "MediaPipe -> inferFaceEmotion (browser)",
                    "Text + Face -> fuse_emotions -> fusion_note",
                    "Pinecone RAG + session DB fallback -> prompt",
                    "Ollama LLM -> streamed reply",
                    "MediaPipe -> avatar animation (parallel)",
                ],
                "known_limits": [
                    "Face emotion is heuristic from geometry, not a trained classifier",
                    "Ollama latency dominates on CPU (~30-60s)",
                    "Pinecone requires API key; DB fallback covers same session",
                ],
            },
            indent=2,
        )
    )

    print(f"\nResult: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
