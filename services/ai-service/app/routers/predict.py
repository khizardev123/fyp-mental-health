from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

router = APIRouter()

class PredictRequest(BaseModel):
    text: str

@router.post("/emotion")
async def predict_emotion(request: PredictRequest):
    from main import emotion_analyzer
    return emotion_analyzer.predict(request.text)

@router.post("/crisis")
async def predict_crisis(request: PredictRequest):
    from main import crisis_detector
    return crisis_detector.predict(request.text)

@router.post("/mental-health")
async def predict_mhealth(request: PredictRequest):
    from main import mental_health_detector
    return mental_health_detector.predict(request.text)
