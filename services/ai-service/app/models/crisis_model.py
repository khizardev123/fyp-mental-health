import joblib
import logging
import re
from app.core.config import settings

logger = logging.getLogger(__name__)

# The model is now calibrated against the 4-level Crisis Taxonomy:
# Level 1: Emotional / NOT Crisis
# Level 2: Implicit Crisis
# Level 3: Explicit Crisis
# Level 4: Positive Confounders (Safe)
POSITIVE_EMOTIONS = {"joy", "love", "surprise"}

class CrisisDetector:
    """
    Semantic Crisis Detector.
    Analyzes the complete sentence context using a trained TF-IDF + Calibrated LR pipeline.
    Prioritizes model-driven inference over simple keyword triggers.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        try:
            self.pipeline = joblib.load(self.model_path)
            logger.info("✅ Semantic Crisis model loaded")
        except Exception as e:
            logger.error(f"Crisis model load failed: {e}")
            raise

    def predict(self, text: str, emotion: str = "neutral", emotion_confidence: float = 0.0, history: list = None) -> dict:
        """
        Analyzes the complete sentence context provided in 'text'.
        Factoring in the conversation history for 'Contextual Smoothing'.
        """
        text_lower = text.lower()
        
        # ── Step 0: Contextual Sensitivity Analysis ──────────────────────────
        # If history shows previous high risks, we increase the current sensitivity
        history_boost = 0.0
        if history:
            # Check last N messages in history
            recent_context = history[-settings.HISTORY_LOOKBACK:]
            prev_crisis_count = sum(1 for msg in recent_context if 
                                    isinstance(msg, dict) and 
                                    msg.get('analysis', {}).get('risk_level') in ('HIGH', 'CRISIS'))
            
            if prev_crisis_count > 0:
                history_boost = settings.CONTEXT_SENSITIVITY_BOOST * prev_crisis_count
                logger.info(f"Contextual Smoothing: Boosting sensitivity by {history_boost}")

        try:
            # Model analyzes complete sentence (word n-grams + char n-grams)
            probs = self.pipeline.predict_proba([text])[0]
            classes = list(self.pipeline.classes_)
            crisis_idx = classes.index(1) if 1 in classes else -1
            raw_prob = float(probs[crisis_idx]) if crisis_idx != -1 else 0.0
        except Exception as e:
            logger.error(f"Crisis prediction failed: {e}")
            raw_prob = 0.02

        # ── Step 1: Reliability Bridge (Explicit Keyword Check) ──────────────
        # This ensures we don't lose credibility on blunt, explicit threats
        # that the lightweight semantic model might not have sufficient weight for.
        explicit_boost = 0.0
        for keyword in settings.EXPLICIT_KEYWORDS:
            if keyword in text_lower:
                explicit_boost = max(explicit_boost, 0.85) # Force CRISIS level
                logger.info(f"Reliability Bridge: Triggered by explicit keyword '{keyword}'")
                break

        # ── Step 2: Subtle calibration for positive emotional context ────────
        combined_prob = max(raw_prob, explicit_boost)
        calibrated_prob = min(0.98, combined_prob + history_boost)
        
        # Only discount if it's NOT an explicit threat (triggered by reliability bridge)
        if explicit_boost == 0 and emotion in POSITIVE_EMOTIONS and emotion_confidence >= 0.50 and raw_prob < 0.70:
            discount = min(0.50, emotion_confidence * 0.6)
            calibrated_prob = raw_prob * (1.0 - discount)

        calibrated_prob = round(calibrated_prob, 4)

        # Map probability to risk levels based on centralized taxonomy thresholds
        if calibrated_prob >= settings.THRESHOLD_CRISIS:
            risk_level, action = "CRISIS", True
        elif calibrated_prob >= settings.THRESHOLD_HIGH:
            risk_level, action = "HIGH", True
        elif calibrated_prob >= settings.THRESHOLD_MEDIUM:
            risk_level, action = "MEDIUM", False
        else:
            risk_level, action = "LOW", False

        return {
            "crisis_probability": calibrated_prob,
            "risk_level": risk_level,
            "requires_immediate_action": action,
            "triggered_by": "semantic_model",
            "full_context_analysis": True,
            "raw_probability": round(raw_prob, 4)
        }
