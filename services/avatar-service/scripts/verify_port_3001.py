"""Verify SereneMind frontend on port 3001."""
import asyncio
import json
import sys
from pathlib import Path

import httpx

FRONT = "http://127.0.0.1:3001"
BASE = "http://127.0.0.1:8001"
MAIN = "http://127.0.0.1:3000"
TIMEOUT = 180.0

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


async def main() -> int:
    print("=" * 60)
    print("SereneMind Port 3001 Verification")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Main site untouched
        try:
            r = await client.get(MAIN, timeout=10)
            record("Main website still on :3000", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            record("Main website still on :3000", False, str(e))

        # Dashboard
        r = await client.get(f"{FRONT}/dashboard", timeout=90)
        record("Dashboard loads", r.status_code == 200, f"bytes={len(r.text)}")

        # Chat via frontend proxy (Ollama)
        r = await client.post(f"{FRONT}/api/chat/message", json={"message": "Hi"}, timeout=TIMEOUT)
        d = r.json()
        record("Ollama chat via proxy", r.status_code == 200 and d.get("reply"), d.get("source", ""))

        # Stream
        events = []
        async with client.stream("POST", f"{FRONT}/api/chat/message/stream", json={"message": "Hello"}, timeout=TIMEOUT) as s:
            async for line in s.aiter_lines():
                if line.startswith("event: "):
                    events.append(line[7:].strip())
        record("Streaming chat", "done" in events and "chunk" in events, str(events[:4]))

        # RAG memory
        g = await client.post(f"{FRONT}/api/chat/message", json={"message": "Hi"}, timeout=TIMEOUT)
        sid = g.json().get("session_id")
        await client.post(f"{FRONT}/api/chat/message", json={"session_id": sid, "message": "I failed an exam last semester"}, timeout=TIMEOUT)
        m = await client.post(f"{FRONT}/api/chat/message", json={"session_id": sid, "message": "My exams are next week"}, timeout=TIMEOUT)
        md = m.json()
        record("Pinecone RAG", md.get("memories_used", 0) >= 1, f"memories={md.get('memories_used')}")

        # TTS + lipsync via proxy
        sample = (md.get("reply") or "Hello")[:100]
        tts = await client.post(f"{FRONT}/api/avatar/speak", json={"text": sample}, timeout=60)
        td = tts.json()
        record("TTS via proxy", tts.status_code == 200 and td.get("url"), td.get("provider", ""))
        lip = await client.post(f"{FRONT}/api/avatar/lipsync", json={"text": sample}, timeout=15)
        record("Lipsync via proxy", len(lip.json().get("timings", [])) > 0)

        # Avatar fusion
        fuse = await client.post(f"{FRONT}/api/avatar/fuse-emotion", json={"text_emotion": "anxiety", "face_confidence": 0.5}, timeout=10)
        record("Avatar emotion fusion", bool(fuse.json().get("final_avatar_emotion")), fuse.json().get("final_avatar_emotion", ""))

        # Analytics page content (dashboard includes analytics panel)
        record("Analytics panel in dashboard", "Life Analytics" in r.text or "Analytics" in r.text)

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nResults: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
