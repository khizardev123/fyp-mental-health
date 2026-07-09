import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/serenemind.db"
    AI_SERVICE_URL: str = "http://127.0.0.1:8000"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_PROVIDER: str = "auto"  # auto | openai | pinecone
    PINECONE_EMBED_MODEL: str = "multilingual-e5-large"
    HISTORY_WINDOW: int = 6
    AVATAR_EMOTION_WINDOW: int = 5
    SESSION_SUMMARY_INTERVAL: int = 20
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_DAYS: int = 7
    AUTH_DISABLED: bool = False
    # Shared secret for POST /auth/provision (Next.js → avatar-service user sync).
    # When empty, provision is restricted to localhost only.
    INTERNAL_PROVISION_SECRET: str | None = None
    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX_NAME: str = "serenemind-memories"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    PINECONE_DIMENSION: int = 1024
    PINECONE_ENABLED: bool = False
    RAG_TOP_K: int = 8
    RAG_RETRIEVE_K: int = 20
    RAG_CATEGORY_TOP_K: int = 6
    RAG_SESSION_MEMORY_LIMIT: int = 24
    RAG_SIMILARITY_THRESHOLD: float = 0.72
    RAG_RECALL_THRESHOLD: float = 0.55
    RAG_FACTUAL_THRESHOLD: float = 0.58
    RAG_PREFERENCE_THRESHOLD: float = 0.58
    RAG_EMOTIONAL_THRESHOLD: float = 0.68
    PROMPT_MAX_SUMMARY_CHARS: int = 400

    # Ollama (local LLM for chat — replaces OpenAI chat)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_FALLBACK_MODEL: str = "mistral"
    OLLAMA_ENABLED: bool = True
    OLLAMA_MAX_TOKENS: int = 90
    OLLAMA_MAX_TOKENS_CRISIS: int = 140

    @property
    def pinecone_active(self) -> bool:
        key = (self.PINECONE_API_KEY or "").strip()
        if not key or "PASTE" in key.upper() or key.endswith("_HERE"):
            return False
        # Auto-enable when a real API key is present (even if PINECONE_ENABLED=false was left in template)
        return self.PINECONE_ENABLED or len(key) >= 20

    @property
    def openai_active(self) -> bool:
        key = (self.OPENAI_API_KEY or "").strip()
        return bool(key and not key.startswith("sk-placeholder"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
