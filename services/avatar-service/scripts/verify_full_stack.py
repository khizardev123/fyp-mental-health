"""Full stack verification for SereneMind demo readiness."""
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE = "http://127.0.0.1:8001"
AI = "http://127.0.0.1:8000"
FRONT = os.environ.get("FRONTEND_URL", "http://127.0.0.1:3001")
OLLAMA = "http://127.0.0.1:11434"
TIMEOUT = 180.0

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


async def stream_turn(client: httpx.AsyncClient, message: str, session_id: str | None) -> dict:
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    events: list[str] = []
    chunks: list[str] = []
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
                events.append(et)
                parsed = json.loads(data)
                if et == "chunk":
                    chunks.append(parsed.get("c", ""))
                if et == "done":
                    final = parsed
    return {"events": events, "chunks": chunks, "final": final, "reply": final.get("reply", ""), "session_id": final.get("session_id")}


async def main() -> int:
    print("=" * 70)
    print("SereneMind Full Stack Verification")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        print("\n--- Infrastructure ---")
        try:
            r = await client.get(f"{OLLAMA}/api/tags", timeout=10)
            models = [m["name"] for m in r.json().get("models", [])]
            record("Ollama running", r.status_code == 200, str(models))
        except Exception as exc:
            record("Ollama running", False, str(exc))

        for url, name in [
            (f"{AI}/health", "AI service health"),
            (f"{AI}/health/ready", "AI service ready"),
            (f"{BASE}/health/ready", "Avatar service ready"),
            (f"{FRONT}/dashboard", "Frontend dashboard"),
        ]:
            try:
                r = await client.get(url, timeout=90)
                record(name, r.status_code == 200, f"status={r.status_code}")
            except Exception as exc:
                record(name, False, str(exc))

        ready = await client.get(f"{BASE}/health/ready", timeout=15)
        rd = ready.json()
        record("Ollama connected (avatar)", rd.get("ollama") is True, f"model={rd.get('ollama_model')}")
        record("Database connected", rd.get("database") is True)

        print("\n--- Auth ---")
        email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
        reg = await client.post(f"{BASE}/auth/register", json={"name": "Verify User", "email": email, "password": "testpass123"}, timeout=15)
        record("Auth register", reg.status_code == 200 and reg.json().get("token"), f"status={reg.status_code}")
        login = await client.post(f"{BASE}/auth/login", json={"email": email, "password": "testpass123"}, timeout=15)
        record("Auth login", login.status_code == 200 and login.json().get("token"), f"status={login.status_code}")
        auth_token = login.json().get("token") or reg.json().get("token")
        auth_headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

        print("\n--- Chat + ML + Pinecone ---")
        session_id = None

        print("  Turn: Greeting")
        g = await stream_turn(client, "Hi", session_id)
        session_id = g["session_id"]
        record("Greeting stream", "done" in g["events"] and "chunk" in g["events"], g["reply"][:70])
        record("Greeting no stale memory", g["final"].get("memories_used", 99) == 0, f"memories={g['final'].get('memories_used')}")
        record("Greeting single done", g["events"].count("done") == 1)

        print("  Turn: Emotional")
        e = await stream_turn(client, "I feel stressed because of exams", session_id)
        session_id = e["session_id"]
        record("Emotional reply", len(e["reply"]) > 20, e["reply"][:80])
        record("ML analysis present", bool(e["final"].get("analysis")), f"emotion={e['final'].get('emotion')}")
        record("Avatar emotion set", bool(e["final"].get("avatar_emotion") or e["final"].get("text_emotion")))

        print("  Turn: Memory seed")
        await stream_turn(client, "Last semester I failed my math exam badly", session_id)
        m = await stream_turn(client, "My exams are next week and I'm worried", session_id)
        session_id = m["session_id"]
        record("Memory RAG retrieval", m["final"].get("memories_used", 0) >= 1, f"memories={m['final'].get('memories_used')}")

        print("  Turn: Crisis")
        c = await client.post(f"{BASE}/chat/message", json={"message": "I feel hopeless and want to give up"}, timeout=TIMEOUT)
        cd = c.json()
        record("Crisis detection HIGH", cd.get("crisis") in ("HIGH", "CRISIS") or cd.get("show_crisis"), f"crisis={cd.get('crisis')}")

        print("\n--- Avatar: TTS + Lipsync + Fusion ---")
        sample = (m["reply"] or "Hello from SereneMind")[:120]
        speak = await client.post(f"{BASE}/avatar/speak", json={"text": sample}, timeout=60)
        sd = speak.json()
        record("TTS generation", speak.status_code == 200 and sd.get("url"), sd.get("provider", ""))
        lip = await client.post(f"{BASE}/avatar/lipsync", json={"text": sample}, timeout=15)
        ld = lip.json()
        record("Lipsync timings", len(ld.get("timings", [])) > 0, f"words={len(ld.get('timings', []))}")
        fuse = await client.post(f"{BASE}/avatar/fuse-emotion", json={"text_emotion": "anxiety", "face_emotion": "sad", "face_confidence": 0.75}, timeout=10)
        fd = fuse.json()
        record("Emotion fusion", bool(fd.get("final_avatar_emotion")), str(fd.get("final_avatar_emotion")))
        face = await client.post(f"{BASE}/avatar/analyze-face", json={"image": ""}, timeout=10)
        record("Face emotion endpoint", face.status_code == 200, f"deepface={face.json().get('available')}")

        print("\n--- Frontend proxy ---")
        try:
            r_dash = await client.get(f"{FRONT}/dashboard", timeout=90)
            record("Dashboard page", r_dash.status_code == 200, f"bytes={len(r_dash.text)}")
            r_proxy = await client.post(
                f"{FRONT}/api/chat/message",
                json={"message": "Hi dashboard test"},
                headers=auth_headers,
                timeout=TIMEOUT,
            )
            pd = r_proxy.json() if r_proxy.headers.get("content-type", "").startswith("application/json") else {}
            record(
                "Frontend chat proxy",
                r_proxy.status_code == 200 and bool(pd.get("reply")),
                pd.get("source", f"status={r_proxy.status_code}"),
            )
            r_stream = await client.post(
                f"{FRONT}/api/chat/message/stream",
                json={"message": "Hello stream test"},
                headers=auth_headers,
                timeout=TIMEOUT,
            )
            record("Frontend stream proxy", r_stream.status_code == 200, f"status={r_stream.status_code}")
        except Exception as exc:
            record("Frontend proxy", False, str(exc))

        # Pinecone indirect: memory retrieval already tested above
        record("Pinecone RAG (via memory test)", m["final"].get("memories_used", 0) >= 1, "see Memory RAG retrieval")

    print("\n" + "=" * 70)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    failed = [(n, d) for n, ok, d in results if not ok]
    if failed:
        print("\nFailed:")
        for n, d in failed:
            print(f"  - {n}: {d}")
    print("=" * 70)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
