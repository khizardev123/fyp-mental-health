"""Text-to-speech: pyttsx3 (offline) with gTTS fallback."""

import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIO_DIR = Path("data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def generate_speech(text: str) -> dict:
    """
    Generate speech audio file.
    Returns { filename, url, format, provider }
    """
    clean = (text or "").strip()[:800]
    if not clean:
        raise ValueError("Text is required for TTS")

    # Try pyttsx3 first (offline, WAV)
    try:
        import pyttsx3

        filename = f"{uuid.uuid4().hex}.wav"
        filepath = AUDIO_DIR / filename
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.save_to_file(clean, str(filepath))
        engine.runAndWait()
        if filepath.exists() and filepath.stat().st_size > 0:
            logger.info("[TTS] pyttsx3 generated %s", filename)
            return {
                "filename": filename,
                "url": f"/api/avatar/audio/{filename}",
                "format": "wav",
                "provider": "pyttsx3",
            }
    except Exception as exc:
        logger.warning("[TTS] pyttsx3 failed: %s — trying gTTS", exc)

    # gTTS fallback (MP3, requires network)
    try:
        from gtts import gTTS

        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename
        gTTS(text=clean, lang="en").save(str(filepath))
        logger.info("[TTS] gTTS generated %s", filename)
        return {
            "filename": filename,
            "url": f"/api/avatar/audio/{filename}",
            "format": "mp3",
            "provider": "gtts",
        }
    except Exception as exc:
        logger.error("[TTS] gTTS failed: %s", exc)
        raise RuntimeError(f"TTS generation failed: {exc}") from exc
