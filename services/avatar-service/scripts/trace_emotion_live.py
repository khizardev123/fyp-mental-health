#!/usr/bin/env python3
"""Trace emotion fields through live pipeline stages for one message."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from app.chat_repository import build_analysis_payload
from app.emotion_pipeline import finalize_emotion_analysis, apply_emotion_context_rules
from app.core.config import settings

MESSAGE = "I failed one subject last semester and my exams are next week."

FIELDS = (
    "raw_label",
    "emotion",
    "mental_state",
    "severity_rating",
    "semantic_summary",
    "tags",
    "emotion_rules_applied",
)


def dump(stage: str, obj: dict) -> None:
    print(f"\n--- {stage} ---")
    for k in FIELDS:
        v = obj
        for part in k.split("."):
            v = v.get(part, {}) if isinstance(v, dict) else None
        if k == "tags" or k == "emotion_rules_applied":
            print(f"  {k}: {v}")
        elif k == "semantic_summary":
            s = str(v or "")[:100]
            print(f"  {k}: {s}")
        else:
            print(f"  {k}: {v}")
    if "unified" in obj:
        u = obj["unified"]
        print("  [nested unified.severity_rating]:", u.get("severity_rating") if isinstance(u, dict) else u)
        print("  [nested unified.semantic_summary]:", str((u.get("semantic_summary") if isinstance(u, dict) else ""))[:80])


async def main() -> None:
    print("=" * 70)
    print("LIVE EMOTION TRACE")
    print("Message:", MESSAGE)
    print("=" * 70)

    # Stage 1: ai-service
    ai_url = f"{settings.AI_SERVICE_URL.rstrip('/')}/analyze/journal"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(ai_url, json={"text": MESSAGE, "history": []})
            r.raise_for_status()
            ml_raw = r.json()
    except Exception as exc:
        print("ai-service unavailable:", exc)
        ml_raw = {}

    dump("1. ai-service response (top-level)", ml_raw)
    if ml_raw.get("unified"):
        dump("1b. ai-service unified", ml_raw["unified"])

    # Stage 2: build_analysis_payload
    payload = build_analysis_payload(ml_raw)
    dump("2. build_analysis_payload", payload)
    print("  [has nested unified?]:", "unified" in payload)

    # Stage 3: finalize
    finalized = apply_emotion_context_rules(MESSAGE, payload)
    dump("3. finalize_emotion_analysis (avatar)", finalized)
    print("  [has nested unified?]:", "unified" in finalized)

    # Consistency check
    print("\n--- CONSISTENCY CHECK ---")
    rl = finalized.get("raw_label")
    sev = finalized.get("severity_rating")
    summ = str(finalized.get("semantic_summary", ""))
    ms = finalized.get("mental_state")
    inconsistent = (
        rl in ("stress", "anxiety")
        and (sev is not None and sev <= 2 or "Routine wellness" in summ or "emotionally stable" in summ.lower())
    )
    print(f"  mental_state={ms} raw_label={rl} severity={sev}")
    print(f"  INCONSISTENT: {inconsistent}")

    if inconsistent:
        print("\n  >>> BUG REPRODUCED IN PIPELINE <<<")
    else:
        print("\n  Pipeline output is internally consistent.")

    # Check if spreading ml_raw into analysis would cause bug
    polluted = {**ml_raw, **payload}
    polluted_fin = apply_emotion_context_rules(MESSAGE, polluted)
    dump("4. IF ml_raw merged into analysis (bug simulation)", polluted_fin)
    inconsistent2 = (
        polluted_fin.get("raw_label") in ("stress", "anxiety")
        and polluted_fin.get("severity_rating", 99) <= 2
    )
    print(f"  INCONSISTENT after ml_raw merge: {inconsistent2}")


if __name__ == "__main__":
    asyncio.run(main())
