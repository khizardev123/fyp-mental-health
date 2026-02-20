import joblib
import logging
from typing import Dict
import os

logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    """Ultra-lightweight Emotion analysis model."""

    EMOTION_EMOJI = {
        0: "😢", # sadness
        1: "😊", # joy
        2: "❤️", # love
        3: "😠", # anger
        4: "😨", # fear
        5: "😲", # surprise
    }
    
    EMOTION_MAP = {0: "sadness", 1: "joy", 2: "love", 3: "anger", 4: "fear", 5: "surprise"}

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading fast emotion model from {self.model_path}")
            self.pipeline = joblib.load(self.model_path)
            logger.info("✅ Emotion model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load emotion model: {e}")
            raise

    def predict(self, text: str) -> Dict:
        try:
            if len(text) > 512:
                text = text[:512]

            probs = self.pipeline.predict_proba([text])[0]
            classes = self.pipeline.classes_
            
            scores = {str(cls): round(float(prob), 4) for cls, prob in zip(classes, probs)}
            top_class = self.pipeline.predict([text])[0]
            top_confidence = scores[str(top_class)]

            emotion_name = self.EMOTION_MAP.get(top_class, "neutral")

            return {
                "emotion": emotion_name,
                "confidence": top_confidence,
                "emoji": self.EMOTION_EMOJI.get(top_class, "💭"),
                "all_scores": {self.EMOTION_MAP.get(int(k), k): v for k, v in scores.items()}
            }
        except Exception as e:
            logger.error(f"Emotion prediction failed: {e}")
            return {"emotion": "neutral", "confidence": 0.5, "emoji": "💭", "all_scores": {"neutral": 0.5}}
