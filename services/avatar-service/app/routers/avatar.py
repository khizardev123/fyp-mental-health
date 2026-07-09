from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from app.response_generator import generate_avatar_response
from app.services.emotion_fusion import fuse_emotions
from app.services.face_emotion import analyze_face_image, get_deepface_status
from app.services.lipsync_service import estimate_mouth_timings
from app.services.tts_service import AUDIO_DIR, generate_speech

router = APIRouter()


class AvatarRequest(BaseModel):
    journal_text: str
    emotion: str
    confidence: float
    risk_level: str
    crisis_probability: Optional[float] = 0.0
    mental_state: Optional[str] = "normal"
    mental_health_confidence: Optional[float] = 0.0
    severity_rating: Optional[int] = 0
    tags: Optional[List[str]] = []
    semantic_summary: Optional[str] = ""
    conversation_history: Optional[List[Dict]] = None


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=800)


class LipsyncRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class AnalyzeFaceRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded webcam frame")


class FuseEmotionRequest(BaseModel):
    text_emotion: str
    face_emotion: Optional[str] = None
    face_confidence: float = 0.0


@router.post("/respond")
async def respond(request: AvatarRequest):
    return generate_avatar_response(
        journal_text=request.journal_text,
        emotion=request.emotion,
        confidence=request.confidence,
        risk_level=request.risk_level,
        crisis_probability=request.crisis_probability or 0.0,
        mental_state=request.mental_state or "normal",
        mental_health_confidence=request.mental_health_confidence or 0.0,
        severity_rating=request.severity_rating or 0,
        tags=request.tags or [],
        semantic_summary=request.semantic_summary or "",
        conversation_history=request.conversation_history,
    )


@router.post("/speak")
async def speak(request: SpeakRequest):
    try:
        result = generate_speech(request.text.strip())
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    media = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(filepath, media_type=media)


@router.post("/lipsync")
async def lipsync(request: LipsyncRequest):
    return estimate_mouth_timings(request.text.strip())


@router.get("/face-status")
async def face_status():
    """Report DeepFace availability for dashboard diagnostics."""
    return get_deepface_status()


@router.post("/analyze-face")
async def analyze_face(request: AnalyzeFaceRequest):
    return analyze_face_image(request.image)


@router.post("/fuse-emotion")
async def fuse_emotion(request: FuseEmotionRequest):
    return fuse_emotions(
        text_emotion=request.text_emotion,
        face_emotion=request.face_emotion,
        face_confidence=request.face_confidence,
    )
