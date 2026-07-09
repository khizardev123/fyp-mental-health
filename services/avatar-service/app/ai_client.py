import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def analyze_text(text: str, history: list[dict] | None = None) -> dict[str, Any]:
    """Call AI service for silent ML analysis."""
    payload = {"text": text, "history": history or []}
    url = f"{settings.AI_SERVICE_URL.rstrip('/')}/analyze/journal"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
