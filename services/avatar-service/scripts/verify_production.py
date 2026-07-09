"""Production quality verification — emotion rules, RAG, pipeline."""
import asyncio
import sys
import time
from pathlib import Path

import httpx

AI = "http://127.0.0.1:8000"
BASE = "http://127.0.0.1:8001"
FRONT = "http://127.0.0.1:3001"
TIMEOUT = 180.0

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


async def analyze(client: httpx.AsyncClient, text: str) -> dict:
    r = await client.post(f"{AI}/analyze/journal", json={"text": text, "history": []}, timeout=30)
    r.raise_for_status()
    return r.json().get("unified") or r.json()


async def chat(client: httpx.AsyncClient, message: str, session_id: str | None = None) -> dict:
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    r = await client.post(f"{BASE}/chat/message", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


async def main() -> int:
    print("=" * 65)
    print("SereneMind Production Quality Verification")
    print("=" * 65)

    async with httpx.AsyncClient() as client:
        print("\n--- ML Emotion Mapping ---")
        cases = [
            ("I am not happy right now", lambda u: u.get("emotion") != "joy" and u.get("raw_label") != "joy",
             "not joy"),
            ("I feel stressed about my exams next week", lambda u: u.get("raw_label") in ("stress", "anxiety"),
             "stress/anxiety not depression"),
            ("I failed my exam last semester", lambda u: u.get("raw_label") in ("stress", "anxiety", "depression")
             and u.get("severity_rating", 10) <= 7, "moderate severity"),
            ("I feel overwhelmed with deadlines but I am coping", lambda u: u.get("raw_label") != "depression",
             "stress not depression"),
        ]
        for text, check, label in cases:
            try:
                u = await analyze(client, text)
                ok = check(u)
                record(f"ML: {label}", ok, f"label={u.get('raw_label')} emotion={u.get('emotion')} sev={u.get('severity_rating')}")
            except Exception as exc:
                record(f"ML: {label}", False, str(exc))

        print("\n--- RAG + Chat ---")
        g = await chat(client, "Hi")
        sid = g["session_id"]
        await chat(client, "Last semester I failed my math exam badly", sid)
        time.sleep(2)
        m = await chat(client, "My exams are next week and I'm worried", sid)
        record("RAG memories retrieved", m.get("memories_used", 0) >= 1, f"memories={m.get('memories_used')}")
        record("Ollama reply", bool(m.get("reply")), m.get("source", ""))

        print("\n--- DeepFace + Fusion ---")
        fs = await client.get(f"{BASE}/avatar/face-status", timeout=10)
        fd = fs.json()
        record("DeepFace status endpoint", fs.status_code == 200, f"available={fd.get('available')}")
        fuse = await client.post(f"{BASE}/avatar/fuse-emotion", json={"text_emotion": "sadness", "face_emotion": "sad", "face_confidence": 0.8}, timeout=10)
        record("Emotion fusion", bool(fuse.json().get("final_avatar_emotion")), fuse.json().get("final_avatar_emotion", ""))

        print("\n--- Frontend proxy ---")
        r = await client.get(f"{FRONT}/dashboard", timeout=90)
        record("Dashboard :3001", r.status_code == 200)

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nResults: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
