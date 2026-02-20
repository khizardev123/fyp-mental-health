from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    user_id: Optional[str] = None
    language: Optional[str] = "en"

class EmotionResult(BaseModel):
    emotion: str
    confidence: float
    all_emotions: dict

class CrisisResult(BaseModel):
    crisis_probability: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRISIS
    requires_immediate_action: bool

class MentalHealthResult(BaseModel):
    mental_state: str
    confidence: float
    all_scores: dict

class AnalysisResponse(BaseModel):
    emotion: EmotionResult
    crisis: CrisisResult
    mental_health: MentalHealthResult
    processing_time_ms: float
    language_detected: str

@router.post("/journal", response_model=AnalysisResponse)
async def analyze_journal_entry(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze a journal entry for emotion and crisis indicators.
    Runs all 3 models: emotion → crisis (emotion-calibrated) → mental health.
    """
    start_time = time.time()

    try:
        from main import emotion_analyzer, crisis_detector, mental_health_detector

        # Step 1: Emotion (needed first so we can calibrate crisis)
        emotion_result = emotion_analyzer.predict(request.text)

        # Step 2: Crisis — pass emotion context for calibration
        crisis_result = crisis_detector.predict(
            text=request.text,
            emotion=emotion_result.get("emotion", "neutral"),
            emotion_confidence=emotion_result.get("confidence", 0.0),
        )

        # Step 3: Mental health
        mh_result = mental_health_detector.predict(request.text)

        processing_time = (time.time() - start_time) * 1000

        return AnalysisResponse(
            emotion=EmotionResult(
                emotion=emotion_result["emotion"],
                confidence=round(emotion_result["confidence"], 4),
                all_emotions=emotion_result.get("all_scores", {})
            ),
            crisis=CrisisResult(
                crisis_probability=crisis_result["crisis_probability"],
                risk_level=crisis_result["risk_level"],
                requires_immediate_action=crisis_result["requires_immediate_action"],
            ),
            mental_health=MentalHealthResult(
                mental_state=mh_result["mental_state"],
                confidence=round(mh_result["confidence"], 4),
                all_scores=mh_result.get("all_scores", {})
            ),
            processing_time_ms=round(processing_time, 2),
            language_detected=request.language or "en"
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

