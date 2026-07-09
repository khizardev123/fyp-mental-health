"""Profile SereneMind response pipeline latency across representative messages."""
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"
TIMEOUT = 180.0

MESSAGES = [
    "Hi, how are you?",
    "I feel stressed because of exams next week",
    "I'm trying to stay positive but I'm anxious about failing",
]

STAGE_KEYS = [
    ("message_received_ms", "Message received"),
    ("ml_analysis_ms", "ML analysis"),
    ("intent_detection_ms", "Intent detection"),
    ("pinecone_embed_ms", "Pinecone embed"),
    ("pinecone_query_ms", "Pinecone query"),
    ("memory_filtering_ms", "Memory filtering"),
    ("prompt_construction_ms", "Prompt construction"),
    ("prep_total_ms", "Prep total (pre-stream)"),
    ("meta_emitted_ms", "Meta emitted"),
    ("ollama_probe_ms", "Ollama probe"),
    ("ollama_ttft_ms", "Ollama TTFT"),
    ("ollama_generation_ms", "Ollama generation"),
    ("streaming_ms", "Streaming"),
    ("save_assistant_ms", "Save assistant"),
    ("summary_update_ms", "Summary update"),
    ("avatar_emotion_ms", "Avatar emotion"),
    ("total_ms", "Total response"),
]


async def profile_turn(client: httpx.AsyncClient, message: str, session_id: str | None) -> dict:
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    t0 = time.perf_counter()
    first_chunk_ms = None
    meta_ms = None
    timing: dict = {}
    final: dict = {}

    async with client.stream("POST", f"{BASE}/chat/message/stream", json=payload, timeout=TIMEOUT) as s:
        buf = ""
        async for raw in s.aiter_text():
            buf += raw
            while "\n\n" in buf:
                block, buf = buf.split("\n\n", 1)
                et, data = "message", ""
                for line in block.split("\n"):
                    if line.startswith("event: "):
                        et = line[7:].strip()
                    if line.startswith("data: "):
                        data = line[6:]
                if not data:
                    continue
                parsed = json.loads(data)
                now = (time.perf_counter() - t0) * 1000
                if et == "meta" and meta_ms is None:
                    meta_ms = now
                if et == "chunk" and first_chunk_ms is None:
                    first_chunk_ms = now
                if et == "done":
                    final = parsed
                    timing = parsed.get("pipeline_timing") or {}

    client_total = (time.perf_counter() - t0) * 1000
    timing["client_meta_ms"] = meta_ms or 0
    timing["client_first_chunk_ms"] = first_chunk_ms or 0
    timing["client_total_ms"] = client_total
    return {
        "message": message,
        "session_id": final.get("session_id"),
        "reply_len": len((final.get("reply") or "").strip()),
        "timing": timing,
    }


def print_breakdown(label: str, timing: dict) -> None:
    print(f"\n--- {label} ---")
    width = max(len(name) for _, name in STAGE_KEYS)
    for key, name in STAGE_KEYS:
        val = timing.get(key, 0.0)
        print(f"{name:<{width}} .... {val:>7.1f} ms")
    print(f"{'Client first chunk':<{width}} .... {timing.get('client_first_chunk_ms', 0):>7.1f} ms")
    print(f"{'Client total':<{width}} .... {timing.get('client_total_ms', 0):>7.1f} ms")


def aggregate(timings: list[dict]) -> dict:
    agg: dict[str, float] = {}
    for key, _ in STAGE_KEYS:
        vals = [t.get(key, 0.0) for t in timings if t.get(key) is not None]
        agg[key] = statistics.mean(vals) if vals else 0.0
    agg["client_first_chunk_ms"] = statistics.mean(
        [t.get("client_first_chunk_ms", 0.0) for t in timings]
    )
    agg["client_total_ms"] = statistics.mean([t.get("client_total_ms", 0.0) for t in timings])
    return agg


async def main() -> int:
    print("=" * 60)
    print("SereneMind Pipeline Latency Profile")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{BASE}/health/ready", timeout=15)
            if r.status_code != 200:
                print("FAIL: avatar-service not ready")
                return 1
        except Exception as exc:
            print(f"FAIL: cannot reach avatar-service: {exc}")
            return 1

        session_id = None
        results = []
        for msg in MESSAGES:
            print(f"\nProfiling: {msg[:60]}...")
            result = await profile_turn(client, msg, session_id)
            session_id = result["session_id"]
            print_breakdown(msg[:40], result["timing"])
            results.append(result["timing"])

        avg = aggregate(results)
        print("\n" + "=" * 60)
        print("AVERAGE ACROSS TURNS")
        print("=" * 60)
        print_breakdown("average", avg)

        # Identify bottleneck (exclude zeros for optional stages)
        candidates = [
            (avg.get("prep_total_ms", 0), "prep_total (ML+RAG+DB+prompt)"),
            (avg.get("ollama_ttft_ms", 0), "ollama_ttft"),
            (avg.get("ollama_generation_ms", 0), "ollama_generation"),
            (avg.get("ollama_probe_ms", 0), "ollama_probe"),
            (avg.get("summary_update_ms", 0), "summary_update"),
            (avg.get("ml_analysis_ms", 0), "ml_analysis"),
            (
                avg.get("pinecone_embed_ms", 0)
                + avg.get("pinecone_query_ms", 0)
                + avg.get("memory_filtering_ms", 0),
                "pinecone_retrieval",
            ),
        ]
        bottleneck = max(candidates, key=lambda x: x[0])
        print(f"\nBOTTLENECK: {bottleneck[1]} ({bottleneck[0]:.1f} ms avg)")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
