from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.chat_repository import (
    analysis_from_stored_message,
    create_session,
    get_recent_messages,
)
from app.chat_service import process_chat_message, stream_chat_message
from app.database.models import User
from app.database.session import get_db

router = APIRouter()


class ChatMessageRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=10000)
    face_emotion: str | None = None
    face_confidence: float = Field(0.0, ge=0.0, le=1.0)


class ChatMessageResponse(BaseModel):
    reply: str
    emotion: str
    crisis: str
    mental_state: str
    text: str
    session_id: str
    user_id: str
    intent: str
    avatar_emotion: str
    show_crisis: bool
    source: str
    analysis: dict
    memories_used: int = 0


class SessionCreateResponse(BaseModel):
    session_id: str
    started_at: str | None = None


class SessionEndResponse(BaseModel):
    session_id: str
    dominant_emotion: str
    emotion_transitions: int
    journey: str
    recommendation: str
    emotion_timeline: list[dict] = Field(default_factory=list)
    ended_at: str | None = None


@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await process_chat_message(
            db,
            user=current_user,
            session_id=request.session_id,
            message=request.message.strip(),
            face_emotion=request.face_emotion,
            face_confidence=request.face_confidence,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {exc}") from exc


@router.post("/message/stream")
async def chat_message_stream(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return StreamingResponse(
            stream_chat_message(
                db,
                user=current_user,
                session_id=request.session_id,
                message=request.message.strip(),
                face_emotion=request.face_emotion,
                face_confidence=request.face_confidence,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat stream failed: {exc}") from exc


@router.post("/session", response_model=SessionCreateResponse)
def start_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new logical session without clearing prior chat history (Phase F-4)."""
    session = create_session(db, current_user)
    started = session.started_at.isoformat() if session.started_at else None
    return {"session_id": session.id, "started_at": started}


@router.get("/session/{session_id}/history")
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.database.models import Session as ChatSession

    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = get_recent_messages(db, session_id, limit=50)

    pending_analysis = None
    formatted = []

    for m in messages:
        if m.role == "user":
            pending_analysis = analysis_from_stored_message(m)
            formatted.append({"role": "user", "text": m.content, "analysis": None})
        else:
            formatted.append({
                "role": "avatar",
                "text": m.content,
                "analysis": pending_analysis,
            })
            pending_analysis = None

    return {"session_id": session_id, "messages": formatted}


@router.post("/session/{session_id}/end", response_model=SessionEndResponse)
def end_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """End a chat session and return an emotional summary (Phase F-1)."""
    from app.database.models import Session as ChatSession
    from app.services.session_emotion_summary import end_chat_session

    session = db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        return end_chat_session(db, session, current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Session end failed: {exc}") from exc
