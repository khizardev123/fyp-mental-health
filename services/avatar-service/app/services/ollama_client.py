"""Ollama local LLM client for chat generation (replaces OpenAI chat)."""

import json
import logging
import time
from collections.abc import AsyncIterator

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Reuse connection to Ollama across requests (avoids TCP/TLS setup per message)
_ollama_client: httpx.AsyncClient | None = None
_ollama_ready_cache: tuple[bool, float] | None = None
_OLLAMA_READY_TTL_SEC = 45.0


def _get_ollama_client() -> httpx.AsyncClient:
    global _ollama_client
    if _ollama_client is None or _ollama_client.is_closed:
        _ollama_client = httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=4, max_connections=8),
        )
    return _ollama_client


def _ollama_options(intent: str, temperature: float) -> dict:
    """Tuned for lower latency on local CPU inference."""
    return {
        "temperature": temperature,
        "num_predict": _max_tokens(intent),
        "num_ctx": 2048,
        "top_k": 24,
        "top_p": 0.9,
        "repeat_penalty": 1.08,
    }


def _max_tokens(intent: str) -> int:
    return settings.OLLAMA_MAX_TOKENS_CRISIS if intent == "crisis" else settings.OLLAMA_MAX_TOKENS


async def generate_ollama_chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.55,
    intent: str = "default",
) -> tuple[str, str]:
    model = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "15m",
        "options": _ollama_options(intent, temperature),
    }

    client = _get_ollama_client()
    response = await client.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    content = (data.get("message") or {}).get("content", "").strip()
    if not content:
        raise ValueError("Empty Ollama response")
    logger.info(
        "[Ollama] Response generated | model=%s | chars=%d | max_tokens=%d",
        model,
        len(content),
        _max_tokens(intent),
    )
    return content, f"ollama:{model}"


async def stream_ollama_chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.55,
    intent: str = "default",
) -> AsyncIterator[str]:
    """Yield content tokens as they arrive from Ollama."""
    model = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": "15m",
        "options": _ollama_options(intent, temperature),
    }

    client = _get_ollama_client()
    async with client.stream("POST", url, json=payload) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            token = (data.get("message") or {}).get("content", "")
            if token:
                yield token
            if data.get("done"):
                break


async def is_ollama_available() -> bool:
    """True when Ollama is reachable and at least one configured model is installed."""
    global _ollama_ready_cache
    now = time.monotonic()
    if _ollama_ready_cache and (now - _ollama_ready_cache[1]) < _OLLAMA_READY_TTL_SEC:
        return _ollama_ready_cache[0]

    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        client = _get_ollama_client()
        response = await client.get(url, timeout=5.0)
        if response.status_code != 200:
            _ollama_ready_cache = (False, now)
            return False
        installed = {
            m.get("name", "").split(":")[0].lower()
            for m in response.json().get("models", [])
        }
        primary = settings.OLLAMA_MODEL.split(":")[0].lower()
        fallback = settings.OLLAMA_FALLBACK_MODEL.split(":")[0].lower()
        available = primary in installed or fallback in installed
        if available:
            logger.info("[Ollama] Server ready | models=%s", sorted(installed))
        else:
            logger.warning(
                "[Ollama] Server up but models missing | want=%s/%s | have=%s",
                primary, fallback, sorted(installed),
            )
        _ollama_ready_cache = (available, now)
        return available
    except Exception as exc:
        logger.warning("[Ollama] Unavailable: %s", exc)
        _ollama_ready_cache = (False, now)
        return False


async def generate_chat_with_fallback(
    messages: list[dict[str, str]],
    intent: str,
) -> tuple[str, str]:
    """Try primary model, then fallback, raise if both fail."""
    temp = 0.4 if intent == "crisis" else 0.65
    models = [settings.OLLAMA_MODEL]
    if settings.OLLAMA_FALLBACK_MODEL not in models:
        models.append(settings.OLLAMA_FALLBACK_MODEL)

    last_error: Exception | None = None
    for model in models:
        try:
            return await generate_ollama_chat(
                messages, model=model, temperature=temp, intent=intent
            )
        except Exception as exc:
            last_error = exc
            logger.warning("[Ollama] model %s failed: %s", model, exc)

    raise last_error or RuntimeError("Ollama unavailable")


async def stream_chat_with_fallback(
    messages: list[dict[str, str]],
    intent: str,
) -> AsyncIterator[tuple[str, str]]:
    """Stream tokens; yields (token, source). Raises if all models fail."""
    temp = 0.4 if intent == "crisis" else 0.65
    models = [settings.OLLAMA_MODEL]
    if settings.OLLAMA_FALLBACK_MODEL not in models:
        models.append(settings.OLLAMA_FALLBACK_MODEL)

    last_error: Exception | None = None
    for model in models:
        try:
            source = f"ollama:{model}"
            async for token in stream_ollama_chat(
                messages, model=model, temperature=temp, intent=intent
            ):
                yield token, source
            return
        except Exception as exc:
            last_error = exc
            logger.warning("[Ollama] stream model %s failed: %s", model, exc)

    raise last_error or RuntimeError("Ollama unavailable")
