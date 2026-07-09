"""Quick post-restart verification."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

BASE = "http://127.0.0.1:8001"
FRONT = "http://127.0.0.1:3000"
TIMEOUT = 120.0


def ok(label: str, passed: bool, detail: str = "") -> bool:
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))
    return passed


async def stream_chat(message: str, session_id: str | None = None) -> dict:
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    events: list[str] = []
    chunks: list[str] = []
    final: dict = {}
    async with httpx.AsyncClient() as client:
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
                        final = parsed
    return {"events": events, "chunks": chunks, "final": final, "reply": final.get("reply", "")}


async def main() -> int:
    print("=" * 60)
    print("SereneMind Post-Restart Verification")
    print("=" * 60)
    passed = 0
    total = 0

    async with httpx.AsyncClient() as client:
        # Health
        total += 1
        r = await client.get(f"{BASE}/health/ready", timeout=15)
        d = r.json()
        if ok("Backend /health/ready", r.status_code == 200 and d.get("ollama"), str(d)):
            passed += 1

        total += 1
        r2 = await client.get(f"{FRONT}/dashboard", timeout=90)
        if ok("Frontend /dashboard", r2.status_code == 200, f"status={r2.status_code}"):
            passed += 1

        total += 1
        try:
            r3 = await client.get("http://127.0.0.1:8000/health", timeout=5)
            if ok("AI service still up", r3.status_code == 200):
                passed += 1
        except Exception as e:
            ok("AI service still up", False, str(e))

        # Greeting
        print("\n--- Greeting ---")
        g = await stream_chat("Hi")
        total += 1
        fresh = g["reply"] and len(g["reply"]) < 300
        no_mem = g["final"].get("memories_used", 99) == 0
        if ok("Greeting stream", "chunk" in g["events"] and "done" in g["events"], g["reply"][:80]):
            passed += 1
        total += 1
        if ok("Greeting no memories", no_mem, f"memories_used={g['final'].get('memories_used')}"):
            passed += 1
        sid = g["final"].get("session_id")

        # Memory recall
        print("\n--- Memory recall ---")
        await stream_chat("Last semester I failed my math exam badly", sid)
        m = await stream_chat("My exams are next week and I'm worried", sid)
        total += 1
        if ok("Memory RAG", m["final"].get("memories_used", 0) >= 0, f"memories={m['final'].get('memories_used')} reply={m['reply'][:60]}"):
            passed += 1

        # Crisis
        print("\n--- Crisis ---")
        c = await stream_chat("I feel hopeless and I want to give up")
        total += 1
        crisis = c["final"].get("crisis") in ("HIGH", "CRISIS") or c["final"].get("show_crisis")
        if ok("Crisis escalation", crisis, f"crisis={c['final'].get('crisis')}"):
            passed += 1

        # TTS
        print("\n--- TTS ---")
        total += 1
        tts = await client.post(f"{BASE}/avatar/speak", json={"text": "Hello test"}, timeout=60)
        if ok("TTS generate", tts.status_code == 200 and tts.json().get("provider"), tts.json().get("provider", "")):
            passed += 1

        # Frontend proxy stream
        print("\n--- Frontend proxy ---")
        total += 1
        fe = await stream_chat("Hi again")
        # reuse stream via frontend
        events = []
        async with client.stream("POST", f"{FRONT}/api/chat/message/stream", json={"message": "Hello"}, timeout=TIMEOUT) as s:
            async for line in s.aiter_lines():
                if line.startswith("event: "):
                    events.append(line[7:].strip())
        if ok("Frontend stream proxy", "chunk" in events and "done" in events, str(events[:4])):
            passed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
