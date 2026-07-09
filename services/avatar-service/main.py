from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

from app.database.session import check_db_connection, init_db
from app.routers import auth, avatar, chat
from app.services.ollama_client import is_ollama_available

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clear settings cache on startup so .env changes are picked up
from app.core.config import get_settings
get_settings.cache_clear()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SereneMind Backend (Chat + Auth + Memory) ...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down SereneMind Backend ...")


app = FastAPI(
    title="SereneMind Backend",
    description="Persistent conversational memory, auth, emotional intelligence, and RAG",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(avatar.router, prefix="/avatar", tags=["Avatar"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "serenemind-backend"}


@app.get("/health/ready")
async def readiness():
    if not check_db_connection():
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": False},
        )
    ollama = await is_ollama_available()
    return {
        "status": "ready",
        "database": True,
        "ollama": ollama,
        "ollama_model": get_settings().OLLAMA_MODEL,
        "ollama_fallback": get_settings().OLLAMA_FALLBACK_MODEL,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
