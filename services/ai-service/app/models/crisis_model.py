import joblib
import logging
import re

logger = logging.getLogger(__name__)

# Hard crisis phrases — override model if detected
CRISIS_PHRASES = [
    "kill myself", "want to die", "end my life", "suicide",
    "better off dead", "no reason to live", "self harm", "cant live",
    "life has no meaning", "rather be dead",
]

# Positive/neutral emotion names that strongly discount crisis
POSITIVE_EMOTIONS = {"joy", "love", "surprise"}

class CrisisDetector:
    """
    Crisis detection model with emotion-aware calibration.
    Prevents false positives when emotion is clearly positive.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        try:
            self.pipeline = joblib.load(self.model_path)
            logger.info("✅ Crisis detection model loaded")
        except Exception as e:
            logger.error(f"Crisis model load failed: {e}")
            raise

    def predict(self, text: str, emotion: str = "neutral", emotion_confidence: float = 0.0) -> dict:
        text_lower = text.lower()

        # 1. Hard keyword check — highest priority
        for phrase in CRISIS_PHRASES:
            if phrase in text_lower:
                return {
                    "crisis_probability": 0.95,
                    "risk_level": "CRISIS",
                    "requires_immediate_action": True,
                    "triggered_by": "keyword",
                }

        # 2. Model prediction
        try:
            probs = self.pipeline.predict_proba([text])[0]
            classes = list(self.pipeline.classes_)
            crisis_idx = classes.index(1) if 1 in classes else -1
            raw_prob = float(probs[crisis_idx]) if crisis_idx != -1 else 0.0
        except Exception as e:
            logger.error(f"Crisis prediction failed: {e}")
            raw_prob = 0.05

        # 3. Emotion-aware calibration
        # If dominant emotion is clearly positive, heavily discount crisis score
        calibrated_prob = raw_prob
        if emotion in POSITIVE_EMOTIONS and emotion_confidence >= 0.45:
            # Discount by up to 70% for strong positive emotions
            discount = min(0.70, emotion_confidence * 0.8)
            calibrated_prob = raw_prob * (1.0 - discount)

        elif emotion in {"sadness", "fear"} and emotion_confidence >= 0.70:
            # Slight boost for strong negative emotions (sadness/fear)
            calibrated_prob = min(0.95, raw_prob * 1.15)

        calibrated_prob = round(calibrated_prob, 4)

        # 4. Risk level mapping with calibrated thresholds
        if calibrated_prob >= 0.75:
            risk_level = "CRISIS"
            action = True
        elif calibrated_prob >= 0.55:
            risk_level = "HIGH"
            action = True
        elif calibrated_prob >= 0.35:
            risk_level = "MEDIUM"
            action = False
        else:
            risk_level = "LOW"
            action = False

        return {
            "crisis_probability": calibrated_prob,
            "risk_level": risk_level,
            "requires_immediate_action": action,
            "triggered_by": "model",
            "raw_probability": round(raw_prob, 4),
        }
