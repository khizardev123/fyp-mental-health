import joblib
import logging

logger = logging.getLogger(__name__)

class MentalHealthDetector:
    """
    Mental Health classifier trained on mental_health_conversations.csv.
    Labels are real strings: anxiety, depression, stress, grief, anger, normal
    """

    # Friendly display names
    STATE_DISPLAY = {
        "anxiety":    "Anxiety",
        "depression": "Depression",
        "stress":     "Stress",
        "grief":      "Grief",
        "anger":      "Anger",
        "normal":     "Stable",
    }

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        try:
            self.pipeline = joblib.load(self.model_path)
            logger.info("✅ Mental Health detection model loaded")
        except Exception as e:
            logger.error(f"Mental Health model load failed: {e}")
            raise

    def predict(self, text: str) -> dict:
        try:
            if len(text) > 512:
                text = text[:512]

            probs = self.pipeline.predict_proba([text])[0]
            classes = list(self.pipeline.classes_)

            # Build named scores dict
            all_scores = {cls: round(float(prob), 4) for cls, prob in zip(classes, probs)}

            top_class = self.pipeline.predict([text])[0]
            top_confidence = all_scores[str(top_class)]

            display_name = self.STATE_DISPLAY.get(str(top_class), str(top_class).capitalize())

            return {
                "mental_state": display_name,
                "raw_label": str(top_class),
                "confidence": top_confidence,
                "all_scores": all_scores,
            }
        except Exception as e:
            logger.error(f"Mental health prediction failed: {e}")
            return {
                "mental_state": "Stable",
                "raw_label": "normal",
                "confidence": 0.5,
                "all_scores": {},
            }
