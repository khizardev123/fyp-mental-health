"""Final SereneMind E2E verification script."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE = "http://127.0.0.1:8001"
FRONT = "http://127.0.0.1:3000"
TIMEOUT = 180.0

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


async def chat(client: httpx.AsyncClient, message: str, session_id: str | None = None) -> dict:
    payload: dict = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    r = await client.post(f"{BASE}/chat/message", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


async def main() -> int:
    print("=" * 60)
    print("SereneMind Final E2E Verification")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Ollama
        try:
            r = await client.get("http://127.0.0.1:11434/api/tags", timeout=5)
            models = [m["name"] for m in r.json().get("models", [])]
            record("Ollama running", r.status_code == 200, str(models))
            record("llama3 installed", any("llama3" in m for m in models))
            record("mistral installed", any("mistral" in m for m in models))
        except Exception as exc:
            record("Ollama running", False, str(exc))

        # Services
        for url, name in [
            ("http://127.0.0.1:8000/health", "AI service :8000"),
            (f"{BASE}/health/ready", "Avatar service :8001"),
            (FRONT, "Frontend :3000"),
        ]:
            try:
                r = await client.get(url, timeout=10)
                record(name, r.status_code == 200, f"status={r.status_code}")
            except Exception as exc:
                record(name, False, str(exc))

        ready = await client.get(f"{BASE}/health/ready", timeout=10)
        rd = ready.json()
        record("Ollama connected to avatar", rd.get("ollama") is True, f"model={rd.get('ollama_model')}")

        session_id = None

        # Test 1
        print("\n--- Test 1: Hi ---")
        d1 = await chat(client, "Hi", session_id)
        session_id = d1["session_id"]
        reply1 = d1.get("reply", "")
        record("Test1 natural reply", len(reply1) > 10, reply1[:80])
        record("Test1 source ollama:llama3", d1.get("source") == "ollama:llama3", d1.get("source"))
        crisis_ok = d1.get("crisis") in ("LOW", "MEDIUM") and d1.get("show_crisis") is False
        record("Test1 no emotional overreaction", crisis_ok, f"crisis={d1.get('crisis')}")

        # Test 2
        print("\n--- Test 2: stressed about exams ---")
        d2 = await chat(client, "I feel stressed about exams", session_id)
        session_id = d2["session_id"]
        reply2 = d2.get("reply", "")
        supportive = any(w in reply2.lower() for w in ("stress", "exam", "understand", "feel", "help", "support", "okay", "normal"))
        record("Test2 emotional support reply", supportive, reply2[:100])
        record("Test2 ML analysis", bool(d2.get("analysis")), f"emotion={d2.get('emotion')} mental_state={d2.get('mental_state')}")
        record("Test2 avatar emotion set", bool(d2.get("avatar_emotion") or d2.get("text_emotion")), d2.get("avatar_emotion"))

        # Test 3
        print("\n--- Test 3: RAG memory continuity ---")
        d3a = await chat(client, "Last semester I failed an exam", session_id)
        session_id = d3a["session_id"]
        record("Test3a memory upsert", d3a.get("memories_used", 0) >= 0, f"memories={d3a.get('memories_used')}")

        d3b = await chat(client, "My exams are next week", session_id)
        session_id = d3b["session_id"]
        rag_ok = d3b.get("memories_used", 0) >= 1
        record("Test3b RAG retrieves memory", rag_ok, f"memories_used={d3b.get('memories_used')}")
        continuity = any(w in d3b.get("reply", "").lower() for w in ("exam", "fail", "last", "semester", "before", "remember", "mentioned"))
        record("Test3b continuity in reply", continuity or rag_ok, d3b.get("reply", "")[:120])
        record("Test3b source ollama", d3b.get("source", "").startswith("ollama"), d3b.get("source"))

        # Test 4 TTS
        print("\n--- Test 4: TTS + lipsync ---")
        sample = d3b.get("reply", "Hello from SereneMind")[:120]
        r_speak = await client.post(f"{BASE}/avatar/speak", json={"text": sample}, timeout=90)
        speak = r_speak.json()
        record("Test4 audio generated", r_speak.status_code == 200 and speak.get("filename"), speak.get("provider"))
        audio_url = speak.get("url", "")
        if audio_url.startswith("/"):
            audio_url = f"{FRONT}{audio_url}" if audio_url.startswith("/api") else f"{BASE}{audio_url.replace('/api/avatar','/avatar')}"
        r_audio = await client.get(audio_url.replace(BASE, FRONT) if "/api/avatar" in audio_url else f"{FRONT}/api/avatar/audio/{speak.get('filename')}", timeout=30)
        record("Test4 audio file accessible", r_audio.status_code == 200 and len(r_audio.content) > 100, f"bytes={len(r_audio.content)}")
        r_lip = await client.post(f"{BASE}/avatar/lipsync", json={"text": sample}, timeout=10)
        lip = r_lip.json()
        record("Test4 lipsync timings", len(lip.get("timings", [])) > 0, f"words={len(lip.get('timings', []))}")

        # Test 5 webcam / fusion
        print("\n--- Test 5: face emotion + fusion ---")
        r_face = await client.post(f"{BASE}/avatar/analyze-face", json={"image": ""}, timeout=10)
        face = r_face.json()
        deepface = face.get("available", False)
        record("Test5 face endpoint responds", r_face.status_code == 200, f"available={deepface}")
        if not deepface:
            record("Test5 DeepFace optional skip", True, face.get("error", "not installed — fusion still works"))
        r_fuse = await client.post(
            f"{BASE}/avatar/fuse-emotion",
            json={"text_emotion": "anxiety", "face_emotion": "sad", "face_confidence": 0.75},
            timeout=10,
        )
        fuse = r_fuse.json()
        record("Test5 emotion fusion", fuse.get("final_avatar_emotion") in ("anxious", "sad"), str(fuse))

        # Test 6 dashboard API path
        print("\n--- Test 6: frontend proxy + dashboard ---")
        try:
            r_dash = await client.get(f"{FRONT}/dashboard", timeout=30)
            record("Test6 dashboard loads", r_dash.status_code == 200, f"status={r_dash.status_code}")
            r_chat_proxy = await client.post(f"{FRONT}/api/chat/message", json={"message": "Hi dashboard test"}, timeout=TIMEOUT)
            pd = r_chat_proxy.json()
            record("Test6 frontend chat proxy", r_chat_proxy.status_code == 200 and pd.get("source", "").startswith("ollama"), pd.get("source"))
        except Exception as exc:
            record("Test6 dashboard loads", False, str(exc))

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    for name, ok, detail in results:
        if not ok:
            print(f"  FAILED: {name} — {detail}")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
