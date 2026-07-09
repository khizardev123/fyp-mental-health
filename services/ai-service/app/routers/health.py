from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("")
async def health_check():
    return {"status": "ok", "service": "ai-service"}


@router.get("/ready")
async def readiness_check():
    from main import unified_analyzer

    if unified_analyzer is not None:
        return {"status": "ready", "unified_model": True}
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "unified_model": False},
    )
