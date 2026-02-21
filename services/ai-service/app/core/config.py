import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "SereneMind AI Service"
    DEBUG: bool = False
    
    # Model Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    ML_MODELS_DIR: str = os.path.join(BASE_DIR, "ml", "models")
    
    EMOTION_MODEL_PATH: str = os.path.join(ML_MODELS_DIR, "lightweight_emotion.joblib")
    CRISIS_MODEL_PATH: str = os.path.join(ML_MODELS_DIR, "lightweight_crisis.joblib")
    MH_MODEL_PATH: str = os.path.join(ML_MODELS_DIR, "lightweight_mental_health.joblib")

    # Crisis Sensitivity Thresholds (Aggressive for Recall)
    THRESHOLD_CRISIS: float = 0.60    # Lowered from 0.65
    THRESHOLD_HIGH: float = 0.35      # Lowered from 0.40
    THRESHOLD_MEDIUM: float = 0.18    # Lowered from 0.20
    
    # Reliability Overrides (Fail-safe for Explicit Threats)
    EXPLICIT_KEYWORDS: list = [
        "kill myself", "end my life", "want to die", 
        "hang myself", "take pills", "overdose", 
        "don't want to live", "suicide", "disappear",
        "existing is", "reason to continue",
        "better without me", "pills", "end it all"
    ]
    
    # Contextual Smoothing Settings
    HISTORY_LOOKBACK: int = 3
    CONTEXT_SENSITIVITY_BOOST: float = 0.15

    # Crisis Taxonomy Guidelines (Refined)
    TAXONOMY_GUIDELINES: dict = {
        "Level 1": {
            "description": "Emotional but NOT Crisis",
            "examples": [
                "I failed my exam and I feel terrible but I’ll try again.",
                "Life feels heavy lately but I know this is temporary.",
                "I feel lonely these days but I am working on myself.",
                "I cried today but it helped me release emotions.",
                "Sometimes I feel useless, but I want to improve."
            ],
            "expected_risk": "LOW/MEDIUM"
        },
        "Level 2": {
            "description": "Implicit Crisis",
            "examples": [
                "I don’t see a reason to continue anymore.",
                "Everyone would be better without me.",
                "I wish I could disappear forever.",
                "Nothing matters now.",
                "I am tired of existing."
            ],
            "expected_risk": "HIGH/CRISIS"
        },
        "Level 3": {
            "description": "Explicit Crisis",
            "examples": [
                "I want to kill myself.",
                "I am planning to end my life tonight.",
                "I can’t take it anymore, I want to die.",
                "I searched how to hang myself.",
                "I have pills and I might take them."
            ],
            "expected_risk": "CRISIS"
        },
        "Level 4": {
            "description": "Positive Confounders",
            "examples": [
                "I love life and feel amazing today.",
                "I feel proud and accomplished.",
                "Today was peaceful and beautiful.",
                "I am excited for my future.",
                "Everything feels hopeful."
            ],
            "expected_risk": "SAFE/LOW"
        }
    }

settings = Settings()
