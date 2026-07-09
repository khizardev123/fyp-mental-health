"""Verify streaming sync: one reply per turn, chunks, TTS, no duplicates."""
import asyncio
import json
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"
TIMEOUT = 180.0

MESSAGES = [
    "Hi",
    "I am good, how are you",
    "I feel stressed because of exams",
]


async def stream_turn(client: httpx.AsyncClient, message: str, session_id: str | None) -> dict:
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    events: list[str] = []
    chunks: list[str] = []
    final: dict = {}
    done_count = 0

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
                events.append(et)
                parsed = json.loads(data)
                if et == "chunk":
                    chunks.append(parsed.get("c", ""))
                if et == "done":
                    done_count += 1
                    final = parsed

    streamed = "".join(chunks)
    reply = (final.get("reply") or "").strip()
    return {
        "message": message,
        "events": events,
        "chunk_count": len(chunks),
        "done_count": done_count,
        "streamed": streamed,
        "reply": reply,
        "stream_matches_reply": streamed.strip() == reply or reply.startswith(streamed.strip()),
        "session_id": final.get("session_id"),
        "memories_used": final.get("memories_used"),
        "crisis": final.get("crisis"),
    }


async def main() -> int:
    print("=" * 60)
    print("Sync Flow Verification (3-turn conversation)")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/health/ready", timeout=15)
        if r.status_code != 200:
            print("FAIL: backend not ready")
            return 1
        print("OK: backend ready\n")

        session_id = None
        passed = 0
        total = 0

        for msg in MESSAGES:
            total += 4
            turn = await stream_turn(client, msg, session_id)
            session_id = turn["session_id"]

            ok_single_done = turn["done_count"] == 1
            ok_has_chunks = turn["chunk_count"] >= 1
            ok_reply = bool(turn["reply"])
            ok_stream = turn["stream_matches_reply"] or abs(len(turn["streamed"]) - len(turn["reply"])) < 5

            print(f"--- \"{msg}\" ---")
            print(f"  chunks={turn['chunk_count']} done_events={turn['done_count']}")
            print(f"  reply: {turn['reply'][:90]}...")
            if turn.get("memories_used") is not None:
                print(f"  memories_used={turn['memories_used']}")

            checks = [
                ("single done event", ok_single_done),
                ("phrase chunks emitted", ok_has_chunks),
                ("reply present", ok_reply),
                ("stream matches reply", ok_stream),
            ]
            for label, ok in checks:
                mark = "PASS" if ok else "FAIL"
                print(f"  [{mark}] {label}")
                if ok:
                    passed += 1

            # TTS per turn
            total += 1
            tts = await client.post(f"{BASE}/avatar/speak", json={"text": turn["reply"][:200]}, timeout=60)
            ok_tts = tts.status_code == 200 and tts.json().get("url")
            print(f"  [{'PASS' if ok_tts else 'FAIL'}] TTS for reply")
            if ok_tts:
                passed += 1

            print()

        print("=" * 60)
        print(f"Results: {passed}/{total} passed")
        print("=" * 60)
        return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
