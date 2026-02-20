from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.response_generator import generate_avatar_response

router = APIRouter()

class AvatarRequest(BaseModel):
    journal_text: str
    emotion: str
    confidence: float
    risk_level: str
    crisis_probability: Optional[float] = 0.0
    mental_state: Optional[str] = "normal"
    mental_health_confidence: Optional[float] = 0.0
    conversation_history: Optional[List[Dict[str, str]]] = None

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
        conversation_history=request.conversation_history,
    )
