from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from contextlib import asynccontextmanager
from app.models.emotion_model import EmotionAnalyzer
from app.models.crisis_model import CrisisDetector
from app.models.mental_health_model import MentalHealthDetector
from app.routers import analyze, health, predict
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instances (loaded once at startup)
emotion_analyzer: EmotionAnalyzer = None
crisis_detector: CrisisDetector = None
mental_health_detector: MentalHealthDetector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global emotion_analyzer, crisis_detector, mental_health_detector
    logger.info("🚀 Loading Lightning-Fast AI models...")
    
    # Get absolute path to the ML models directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    models_dir = os.path.join(base_dir, "ml", "models")
    
    emotion_analyzer = EmotionAnalyzer(model_path=os.path.join(models_dir, "lightweight_emotion.joblib"))
    crisis_detector = CrisisDetector(model_path=os.path.join(models_dir, "lightweight_crisis.joblib"))
    mental_health_detector = MentalHealthDetector(model_path=os.path.join(models_dir, "lightweight_mental_health.joblib"))
    
    logger.info("✅ Models loaded successfully")
    yield
    logger.info("🛑 Shutting down AI service...")

app = FastAPI(
    title="SereneMind AI Service",
    description="Emotion analysis and crisis detection for mental health journaling",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(analyze.router, prefix="/analyze", tags=["Analysis"])
app.include_router(predict.router, prefix="/predict", tags=["Predict"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=2)
