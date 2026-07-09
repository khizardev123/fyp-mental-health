"""Optional webcam face emotion via pretrained DeepFace."""

import base64
import logging
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DEEPFACE_TO_AVATAR = {
    "happy": "happy",
    "sad": "sad",
    "angry": "angry",
    "fear": "anxious",
    "surprise": "anxious",
    "disgust": "angry",
    "neutral": "neutral",
}


def get_deepface_status() -> dict:
    """Report whether DeepFace is installed and usable."""
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    try:
        import cv2  # noqa: F401
        opencv_ok = True
    except ImportError:
        opencv_ok = False

    try:
        import deepface  # noqa: F401
        import tensorflow as tf  # noqa: F401
        return {
            "available": True,
            "provider": "deepface",
            "python": py_version,
            "opencv": opencv_ok,
            "tensorflow": tf.__version__,
            "message": "DeepFace ready",
        }
    except ImportError as exc:
        missing = str(exc).replace("No module named ", "").strip("'")
        reason = f"Missing dependency: {missing}"
        if sys.version_info >= (3, 14):
            reason += (
                f" | Python {py_version} is not supported by TensorFlow (required by DeepFace). "
                "Use Python 3.10–3.12 for face emotion."
            )
        return {
            "available": False,
            "provider": None,
            "python": py_version,
            "opencv": opencv_ok,
            "missing_dependency": missing,
            "message": reason,
        }


def analyze_face_image(image_b64: str) -> dict:
    """
    Analyze base64-encoded JPEG/PNG frame.
    Returns { emotion, confidence, raw_emotion, available }
    """
    if not image_b64:
        return {"emotion": "neutral", "confidence": 0.0, "available": False, "error": "No image"}

    try:
        from deepface import DeepFace
    except ImportError:
        logger.warning("[Face] DeepFace not installed — pip install deepface opencv-python-headless")
        return {
            "emotion": "neutral",
            "confidence": 0.0,
            "available": False,
            "error": "DeepFace not installed",
        }

    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_b64)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            result = DeepFace.analyze(
                img_path=tmp_path,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
            )
            if isinstance(result, list):
                result = result[0]

            raw = result.get("dominant_emotion", "neutral")
            scores = result.get("emotion") or {}
            confidence = float(scores.get(raw, 0)) / 100.0
            avatar_emotion = DEEPFACE_TO_AVATAR.get(raw.lower(), "neutral")
            face_detected = bool(result.get("region_emotion") or scores)
            ts = datetime.now(timezone.utc).isoformat()

            logger.info(
                "[Face] ts=%s face_detected=%s emotion=%s confidence=%.3f avatar=%s",
                ts,
                face_detected,
                raw,
                confidence,
                avatar_emotion,
            )
            return {
                "emotion": avatar_emotion,
                "confidence": round(confidence, 3),
                "raw_emotion": raw,
                "face_detected": face_detected,
                "available": True,
                "timestamp": ts,
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as exc:
        logger.warning("[Face] Analysis failed: %s", exc)
        return {
            "emotion": "neutral",
            "confidence": 0.0,
            "available": False,
            "error": str(exc),
        }
