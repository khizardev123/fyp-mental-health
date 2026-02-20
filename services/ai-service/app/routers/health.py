from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def health_check():
    return {"status": "ok", "service": "ai-service"}

@router.get("/ready")
async def readiness_check():
    from main import emotion_analyzer, crisis_detector
    if emotion_analyzer and crisis_detector:
        return {"status": "ready"}
    return {"status": "not_ready"}, 503
