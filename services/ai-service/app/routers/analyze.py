from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request ─────────────────────────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    user_id: Optional[str] = None
    language: Optional[str] = "en"
    history: Optional[list] = []


# ── Response schemas ─────────────────────────────────────────────────────────
class EmotionResult(BaseModel):
    emotion: str
    confidence: float
    all_emotions: dict


class CrisisResult(BaseModel):
    crisis_probability: float
    risk_level: str          # LOW | MEDIUM | HIGH | CRISIS
    requires_immediate_action: bool


class MentalHealthResult(BaseModel):
    mental_state: str
    confidence: float
    all_scores: dict


class UnifiedResult(BaseModel):
    """Full unified model output."""
    mental_state: str
    raw_label: str
    emotion: str
    crisis_risk: str                    # LOW | MEDIUM | HIGH | CRISIS
    crisis_probability: float
    severity_rating: int                # 1–10
    tags: List[str]
    confidence: float
    all_scores: dict
    requires_immediate_action: bool
    semantic_summary: str
    triggered_by: str


class AnalysisResponse(BaseModel):
    # Primary unified output
    unified: UnifiedResult
    # Backward-compatible fields for existing frontend clients
    emotion: EmotionResult
    crisis: CrisisResult
    mental_health: MentalHealthResult
    # Meta
    processing_time_ms: float
    language_detected: str
    model_version: str = "4.0.0"


@router.post("/journal", response_model=AnalysisResponse)
async def analyze_journal_entry(request: AnalysisRequest):
    """
    Analyze a journal entry for emotion, crisis risk, severity, and contextual tags.
    Uses the single Unified Mental Health Model v4 (LogisticRegression + TF-IDF + 3-tier reliability bridge).
    """
    start_time = time.time()

    try:
        from main import unified_analyzer

        if unified_analyzer is None:
            raise RuntimeError("Unified model not loaded — please restart the service.")

        result = unified_analyzer.predict(request.text)

        unified_out = UnifiedResult(
            mental_state              = result["mental_state"],
            raw_label                 = result["raw_label"],
            emotion                   = result["emotion"],
            crisis_risk               = result["crisis_risk"],
            crisis_probability        = result["crisis_probability"],
            severity_rating           = result["severity_rating"],
            tags                      = result["tags"],
            confidence                = result["confidence"],
            all_scores                = result["all_scores"],
            requires_immediate_action = result["requires_immediate_action"],
            semantic_summary          = result["semantic_summary"],
            triggered_by              = result["triggered_by"],
        )

        # Build backward-compat fields so existing frontend doesn't break
        emotion_compat = EmotionResult(
            emotion      = result["emotion"],
            confidence   = result["confidence"],
            all_emotions = result["all_scores"],
        )
        crisis_compat = CrisisResult(
            crisis_probability        = result["crisis_probability"],
            risk_level                = result["crisis_risk"],
            requires_immediate_action = result["requires_immediate_action"],
        )
        mh_compat = MentalHealthResult(
            mental_state = result["mental_state"],
            confidence   = result["confidence"],
            all_scores   = result["all_scores"],
        )

        processing_time = (time.time() - start_time) * 1000

        return AnalysisResponse(
            unified            = unified_out,
            emotion            = emotion_compat,
            crisis             = crisis_compat,
            mental_health      = mh_compat,
            processing_time_ms = round(processing_time, 2),
            language_detected  = request.language or "en",
            model_version      = "4.0.0",
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
