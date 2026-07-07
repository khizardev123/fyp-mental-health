import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.orm import Session

from app.ai_client import analyze_text
from app.chat_repository import (
    build_analysis_payload,
    get_or_create_session,
    get_recent_messages,
    get_session_user_messages,
    messages_to_history,
    rolling_avatar_emotion,
    save_message,
)
from app.core.config import settings
from app.crisis_rules import apply_rule_based_crisis_override, check_rule_based_crisis
from app.emotion_rules import apply_emotion_context_rules
from app.database.models import User
from app.intent_gate import detect_intent
from app.pipeline_profiler import PipelineTiming, log_pipeline_timing
from app.prompt_builder import FRESH_INTENTS, build_prompt_messages, fallback_reply
from app.services.ollama_client import (
    generate_chat_with_fallback,
    is_ollama_available,
    stream_chat_with_fallback,
)
from app.services.summary_service import (
    get_session_summary_text,
    get_user_summary_text,
    maybe_update_summaries,
)
from app.services.memory_retrieval import classify_memory_type, retrieve_memories_for_prompt
from app.services.vector_memory import upsert_memory
from app.services.emotion_fusion import (
    build_fusion_prompt_context,
    fuse_emotions,
)

logger = logging.getLogger(__name__)

# Emit SSE chunks at phrase boundaries (backend batches; frontend renders per frame)
_CHUNK_BOUNDARY = frozenset(" .!?,;\n")
_CHUNK_MAX = 40


def _flush_stream_chunk(buffer: str) -> tuple[str, str]:
    """Split buffer into emit-ready chunk + remainder."""
    if not buffer:
        return "", ""
    for i in range(len(buffer) - 1, -1, -1):
        if buffer[i] in _CHUNK_BOUNDARY:
            return buffer[: i + 1], buffer[i + 1 :]
    if len(buffer) >= _CHUNK_MAX:
        return buffer, ""
    return "", buffer


async def _generate_llm_response(
    messages: list[dict[str, str]], intent: str, analysis: dict[str, Any]
) -> tuple[str, str]:
    if not settings.OLLAMA_ENABLED:
        return fallback_reply(intent, analysis), "template"

    if await is_ollama_available():
        return await generate_chat_with_fallback(messages, intent)

    return fallback_reply(intent, analysis), "template"


async def _prepare_chat_context(
    db: Session,
    *,
    user: User,
    session_id: str | None,
    message: str,
    timing: PipelineTiming,
    face_emotion: str | None = None,
    face_confidence: float = 0.0,
) -> dict[str, Any]:
    """Shared prep: session, ML, RAG, intent, prompt — parallelized where possible."""
    timing.mark("prep")

    t_db = time.perf_counter()
    session = get_or_create_session(db, user, session_id)
    prior_messages = get_recent_messages(db, session.id)
    session_user_messages = get_session_user_messages(db, session.id)
    history = messages_to_history(prior_messages)
    timing.db_session_ms = (time.perf_counter() - t_db) * 1000

    t_intent_pre = time.perf_counter()
    pre_intent = detect_intent(message)
    skip_memory = pre_intent in FRESH_INTENTS
    timing.intent_detection_ms = (time.perf_counter() - t_intent_pre) * 1000

    user_summary = None if skip_memory else get_user_summary_text(db, user.id)
    session_summary = None if skip_memory else get_session_summary_text(session)

    async def _safe_ml() -> dict:
        t_ml = time.perf_counter()
        try:
            ml_history = [] if skip_memory else history
            result = await analyze_text(message, ml_history)
            timing.ml_analysis_ms = (time.perf_counter() - t_ml) * 1000
            return result
        except Exception as exc:
            timing.ml_analysis_ms = (time.perf_counter() - t_ml) * 1000
            logger.warning("ML analysis unavailable: %s", exc)
            return {}

    rag_timings: dict[str, float] = {}

    def _search_memories() -> list[dict]:
        return retrieve_memories_for_prompt(
            user_id=user.id,
            query=message,
            session_id=session.id,
            session_user_messages=session_user_messages,
            timings=rag_timings,
        )

    if skip_memory:
        relevant_memories = []
        ml_raw = await _safe_ml()
    else:
        memories_task = asyncio.to_thread(_search_memories)
        relevant_memories, ml_raw = await asyncio.gather(memories_task, _safe_ml())
        timing.pinecone_embed_ms = rag_timings.get("pinecone_embed_ms", 0.0)
        timing.pinecone_query_ms = rag_timings.get("pinecone_query_ms", 0.0)
        timing.memory_filtering_ms = rag_timings.get("memory_filtering_ms", 0.0)
        timing.memory_retrieval_ms = rag_timings.get("memory_retrieval_ms", 0.0)

    t_rules = time.perf_counter()
    analysis = build_analysis_payload(ml_raw)
    analysis = apply_emotion_context_rules(message, analysis)
    analysis = apply_rule_based_crisis_override(message, analysis)

    fusion = fuse_emotions(
        analysis.get("emotion", "neutral"),
        face_emotion,
        face_confidence,
    )
    fusion_note = build_fusion_prompt_context(
        message=message,
        text_emotion=analysis.get("emotion", "neutral"),
        face_emotion=face_emotion,
        face_confidence=face_confidence,
        fusion=fusion,
    )
    analysis["text_emotion"] = fusion["text_emotion"]
    analysis["face_emotion"] = fusion.get("face_emotion")
    analysis["face_confidence"] = face_confidence
    analysis["fusion_active"] = fusion.get("fusion_active", False)
    analysis["fusion_note"] = fusion_note

    t_intent_post = time.perf_counter()
    intent = detect_intent(message, ml_crisis_level=analysis.get("crisis_risk"))
    rule_level, _ = check_rule_based_crisis(message)
    # Rule-based and explicit crisis always win. ML HIGH/CRISIS must not override greetings.
    if rule_level:
        intent = "crisis"
    elif analysis.get("crisis_risk") in ("HIGH", "CRISIS") and intent not in FRESH_INTENTS:
        intent = "crisis"
    timing.intent_detection_ms += (time.perf_counter() - t_intent_post) * 1000
    timing.emotion_rules_ms = (time.perf_counter() - t_rules) * 1000

    t_save = time.perf_counter()
    user_msg = save_message(
        db,
        session.id,
        role="user",
        content=message,
        emotion=analysis.get("emotion"),
        emotion_confidence=analysis.get("confidence"),
        mental_state=analysis.get("mental_state"),
        mh_confidence=analysis.get("confidence"),
        crisis_score=analysis.get("crisis_probability"),
        crisis_level=analysis.get("crisis_risk"),
        intent=intent,
    )
    timing.save_user_message_ms = (time.perf_counter() - t_save) * 1000

    await asyncio.to_thread(
        upsert_memory,
        user_id=user.id,
        message_id=user_msg.id,
        text=message,
        metadata={
            "session_id": session.id,
            "emotion": analysis.get("emotion"),
            "intent": intent,
            "memory_type": classify_memory_type(message),
            "timestamp": user_msg.timestamp.isoformat() if user_msg.timestamp else "",
        },
    )

    t_prompt = time.perf_counter()
    prompt_messages = build_prompt_messages(
        current_message=message,
        history=[] if intent in FRESH_INTENTS else history,
        analysis=analysis,
        intent=intent,
        user_summary=user_summary,
        session_summary=session_summary,
        relevant_memories=relevant_memories,
        fusion_note=fusion_note,
    )
    timing.prompt_construction_ms = (time.perf_counter() - t_prompt) * 1000
    timing.prep_total_ms = timing.since("prep")

    logger.info(
        "[Pipeline] emotion=%s | mental_state=%s | severity=%s | intent=%s | "
        "face=%s(%.2f) | fusion=%s | memories=%d",
        analysis.get("emotion"),
        analysis.get("mental_state"),
        analysis.get("severity_rating"),
        intent,
        analysis.get("face_emotion"),
        face_confidence,
        analysis.get("fusion_active"),
        len(relevant_memories),
    )
    if relevant_memories:
        for i, mem in enumerate(relevant_memories):
            logger.info(
                "[Pipeline] memory[%d] type=%s | %r",
                i,
                mem.get("memory_type") or (mem.get("metadata") or {}).get("memory_type"),
                (mem.get("text") or "")[:100],
            )
    user_prompt = prompt_messages[-1]["content"] if prompt_messages else ""
    if "Verified memories" in user_prompt:
        mem_block = user_prompt.split("Verified memories", 1)[1].split("\n\nUser:", 1)[0]
        logger.info("[Pipeline] Ollama memory block:%s", mem_block[:500])
    else:
        logger.warning("[Pipeline] Ollama prompt has NO verified memories block | intent=%s", intent)

    return {
        "session": session,
        "analysis": analysis,
        "intent": intent,
        "prompt_messages": prompt_messages,
        "relevant_memories": relevant_memories,
    }


def _build_response_payload(
    *,
    ctx: dict[str, Any],
    reply_text: str,
    source: str,
    db: Session,
    user: User,
    timing: PipelineTiming | None = None,
    avatar_emotion: str | None = None,
) -> dict[str, Any]:
    session = ctx["session"]
    analysis = ctx["analysis"]
    intent = ctx["intent"]

    t_avatar = time.perf_counter()
    text_emotion = avatar_emotion if avatar_emotion is not None else rolling_avatar_emotion(db, session.id)
    if timing is not None:
        timing.avatar_emotion_ms += (time.perf_counter() - t_avatar) * 1000

    # Modal only when intent is crisis — not on ML-only HIGH during greetings/small talk.
    show_crisis = intent == "crisis"

    payload = {
        "reply": reply_text,
        "crisis": analysis.get("crisis_risk", "LOW"),
        "text": reply_text,
        "session_id": session.id,
        "user_id": user.id,
        "intent": intent,
        "avatar_emotion": text_emotion,
        "text_emotion": analysis.get("text_emotion", analysis.get("emotion", "neutral")),
        "face_emotion": analysis.get("face_emotion"),
        "face_confidence": analysis.get("face_confidence", 0.0),
        "fusion_active": analysis.get("fusion_active", False),
        "final_avatar_emotion": text_emotion,
        "show_crisis": show_crisis,
        "source": source,
        "analysis": analysis,
        "memories_used": len(ctx["relevant_memories"]),
        # Top-level mirrors of finalized analysis only (no stale ML fields)
        "emotion": analysis.get("emotion", "neutral"),
        "mental_state": analysis.get("mental_state", "normal"),
        "severity_rating": analysis.get("severity_rating", 0),
        "semantic_summary": analysis.get("semantic_summary", ""),
        "tags": analysis.get("tags", []),
    }
    if timing is not None:
        payload["pipeline_timing"] = timing.to_dict()
    return payload


async def process_chat_message(
    db: Session,
    *,
    user: User,
    session_id: str | None,
    message: str,
    face_emotion: str | None = None,
    face_confidence: float = 0.0,
) -> dict[str, Any]:
    timing = PipelineTiming()
    timing.mark("total")
    timing.message_received_ms = 0.0

    ctx = await _prepare_chat_context(
        db,
        user=user,
        session_id=session_id,
        message=message,
        timing=timing,
        face_emotion=face_emotion,
        face_confidence=face_confidence,
    )

    reply_text, source = await _generate_llm_response(
        ctx["prompt_messages"], ctx["intent"], ctx["analysis"]
    )

    save_message(db, ctx["session"].id, role="assistant", content=reply_text)
    maybe_update_summaries(db, ctx["session"], user.id)

    timing.total_ms = timing.since("total")
    log_pipeline_timing(timing)

    return _build_response_payload(
        ctx=ctx, reply_text=reply_text, source=source, db=db, user=user, timing=timing
    )


async def stream_chat_message(
    db: Session,
    *,
    user: User,
    session_id: str | None,
    message: str,
    face_emotion: str | None = None,
    face_confidence: float = 0.0,
) -> AsyncIterator[str]:
    """
    SSE stream: meta → chunk* → done
    Each yield is a full SSE line block.
    """
    timing = PipelineTiming()
    timing.mark("total")
    timing.message_received_ms = 0.0

    ctx = await _prepare_chat_context(
        db,
        user=user,
        session_id=session_id,
        message=message,
        timing=timing,
        face_emotion=face_emotion,
        face_confidence=face_confidence,
    )

    t_avatar = time.perf_counter()
    avatar_emotion = rolling_avatar_emotion(db, ctx["session"].id)
    timing.avatar_emotion_ms = (time.perf_counter() - t_avatar) * 1000

    meta = _build_response_payload(
        ctx=ctx,
        reply_text="",
        source="streaming",
        db=db,
        user=user,
        timing=timing,
        avatar_emotion=avatar_emotion,
    )
    meta.pop("reply", None)
    meta.pop("text", None)
    timing.meta_emitted_ms = timing.since("total")
    yield f"event: meta\ndata: {json.dumps(meta)}\n\n"

    reply_parts: list[str] = []
    source = "template"

    t_stream = time.perf_counter()
    if settings.OLLAMA_ENABLED:
        t_probe = time.perf_counter()
        ollama_up = await is_ollama_available()
        timing.ollama_probe_ms = (time.perf_counter() - t_probe) * 1000

        if ollama_up:
            try:
                pending = ""
                ollama_started = time.perf_counter()
                first_token = True
                async for token, src in stream_chat_with_fallback(
                    ctx["prompt_messages"], ctx["intent"]
                ):
                    if first_token:
                        timing.ollama_ttft_ms = (time.perf_counter() - ollama_started) * 1000
                        first_token = False
                    reply_parts.append(token)
                    source = src
                    pending += token
                    while True:
                        chunk, pending = _flush_stream_chunk(pending)
                        if not chunk:
                            break
                        yield f"event: chunk\ndata: {json.dumps({'c': chunk})}\n\n"
                if pending:
                    yield f"event: chunk\ndata: {json.dumps({'c': pending})}\n\n"
                timing.ollama_generation_ms = (time.perf_counter() - ollama_started) * 1000
            except Exception as exc:
                logger.error("[Chat] Stream failed: %s", exc)
                fallback = fallback_reply(ctx["intent"], ctx["analysis"])
                reply_parts = [fallback]
                source = "template"
                yield f"event: chunk\ndata: {json.dumps({'c': fallback})}\n\n"
        else:
            fallback = fallback_reply(ctx["intent"], ctx["analysis"])
            reply_parts = [fallback]
            source = "template"
            yield f"event: chunk\ndata: {json.dumps({'c': fallback})}\n\n"
    else:
        fallback = fallback_reply(ctx["intent"], ctx["analysis"])
        reply_parts = [fallback]
        source = "template"
        yield f"event: chunk\ndata: {json.dumps({'c': fallback})}\n\n"

    timing.streaming_ms = (time.perf_counter() - t_stream) * 1000

    reply_text = "".join(reply_parts).strip()
    t_save = time.perf_counter()
    save_message(db, ctx["session"].id, role="assistant", content=reply_text)
    timing.save_assistant_ms = (time.perf_counter() - t_save) * 1000

    t_summary = time.perf_counter()
    maybe_update_summaries(db, ctx["session"], user.id)
    timing.summary_update_ms = (time.perf_counter() - t_summary) * 1000

    timing.total_ms = timing.since("total")
    log_pipeline_timing(timing)

    final = _build_response_payload(
        ctx=ctx,
        reply_text=reply_text,
        source=source,
        db=db,
        user=user,
        timing=timing,
        avatar_emotion=avatar_emotion,
    )
    yield f"event: done\ndata: {json.dumps(final)}\n\n"
