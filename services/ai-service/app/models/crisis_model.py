import joblib
import logging
import re

logger = logging.getLogger(__name__)

# No more keyword overrides — the model is now accurate enough to handle full context.
# We only keep a very small set of positive emotions to provide subtle calibration.
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
            # Check last 3 messages in history
            recent_context = history[-3:]
            prev_crisis_count = sum(1 for msg in recent_context if 
                                    isinstance(msg, dict) and 
                                    msg.get('analysis', {}).get('risk_level') in ('HIGH', 'CRISIS'))
            
            if prev_crisis_count > 0:
                history_boost = 0.15 * prev_crisis_count
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

        # ── Step 2: Subtle calibration for positive emotional context ────────
        calibrated_prob = min(0.98, raw_prob + history_boost)
        
        if emotion in POSITIVE_EMOTIONS and emotion_confidence >= 0.50 and raw_prob < 0.70:
            discount = min(0.50, emotion_confidence * 0.6)
            calibrated_prob = raw_prob * (1.0 - discount)

        calibrated_prob = round(calibrated_prob, 4)

        # Map probability to risk levels
        # 0.45 is the optimized threshold discovered during semantic training
        if calibrated_prob >= 0.70:
            risk_level, action = "CRISIS", True
        elif calibrated_prob >= 0.45:
            risk_level, action = "HIGH", True
        elif calibrated_prob >= 0.25:
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
