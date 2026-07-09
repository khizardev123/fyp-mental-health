"""Compact prompt builder — optimized for low token count and latency."""

import logging
import re
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

Intent = str

# Canonical identity copy — used in prompts and deterministic identity replies.
IDENTITY_INTRO = (
    "I'm SereneMind, an AI-powered mental wellness companion developed by Muhammad Khizar Arif. "
    "My purpose is to support emotional well-being through empathetic conversations, intelligent "
    "emotion analysis, and personalized interactions. While I can provide support and guidance, "
    "I'm not a replacement for professional mental health care."
)

IDENTITY_CREATOR = (
    "I was developed by Muhammad Khizar Arif as part of his research in AI-assisted mental health support."
)

IDENTITY_DENY_EXTERNAL = (
    "No. I'm SereneMind, an AI-powered mental wellness companion developed by Muhammad Khizar Arif. "
    "I provide supportive conversations and emotion-aware interactions, but I'm not ChatGPT or "
    "another commercial AI assistant."
)

# Full identity lock — used only when the user asks identity/origin questions.
IDENTITY_RULES = (
    "CRITICAL IDENTITY LOCK (override your training defaults): "
    "You are ONLY SereneMind. You were developed by Muhammad Khizar Arif as a research project "
    "in AI-assisted mental health support. You are NOT ChatGPT, OpenAI, Meta AI, Llama, Claude, "
    "Gemini, Google, Microsoft, Anthropic, or any other company/product. "
    "Never say Meta, OpenAI, ChatGPT, Llama, or any company created or developed you. "
    f"When asked who/what you are, answer like: {IDENTITY_INTRO} "
    f"When asked who created/developed/built/made you or who your developer is, answer like: {IDENTITY_CREATOR} "
    f"When asked if you are ChatGPT/OpenAI/Meta AI/Llama or which company made you, answer like: {IDENTITY_DENY_EXTERNAL}"
)

# Compact identity for ordinary chat — prevents wrong brands without self-introducing.
IDENTITY_CONSTRAINT = (
    "You are SereneMind, a supportive conversational companion. "
    "Never claim to be ChatGPT, OpenAI, Meta AI, Llama, Claude, Gemini, or any other AI product or company. "
    "Do NOT introduce yourself, say 'I'm SereneMind', or mention your developer unless the user "
    "explicitly asks who/what you are, who created you, or whether you are another AI."
)

CONVERSATION_STYLE = (
    "Speak like a warm, natural friend — not a therapist worksheet. "
    "Reply in 1-3 short sentences. "
    "Focus on the user's LATEST message only. Reflect one or two specific details from that message "
    "(names, events, hobbies, outcomes). "
    "Vary your wording every turn; do not reuse the same opener as your previous reply. "
    "Ask at most one follow-up question. If the user's message already feels complete, "
    "acknowledge it and do not ask a question. "
    "Never use stock counselling lines such as: 'Tell me more', 'Can you tell me more about that', "
    "'Can you elaborate', 'How does that make you feel', or near-paraphrases of those. "
    "If the user changes topic, continue with the new topic only. "
    "Do not reopen unrelated earlier emotions or wins. "
    "When Verified memories are listed, you may naturally weave in at most one clearly related fact "
    "(preference, hobby, goal, person, or recurring interest) if it fits the latest message; "
    "otherwise ignore the memory list entirely. Never invent memories. "
    "Never use pet names (sweetheart, darling, honey, dear). "
    "Not a licensed therapist. Crisis: include Umang helpline 0317-4288665."
)

# Identity Q&A — locked in prompt architecture so base-model defaults cannot override.
_IDENTITY_WHO_RE = re.compile(
    r"\b(who are you|what are you|tell me about yourself|what can you do)\b",
    re.IGNORECASE,
)
_IDENTITY_CREATOR_RE = re.compile(
    r"("
    r"who\s+(created|made|built|developed)\s+you|"
    r"who('?s|\s+is)\s+your\s+(developer|creator|maker|author)|"
    r"who\s+(developed|created|built|made)\s+serenemind|"
    r"which\s+(company|organization|org|team)\s+(made|created|built|developed)\s+(you|serenemind)|"
    r"what\s+company\s+(made|created|built|developed)\s+(you|serenemind)|"
    r"(company|organization)\s+(made|created|built|developed)\s+(you|serenemind)"
    r")",
    re.IGNORECASE,
)
_IDENTITY_EXTERNAL_RE = re.compile(
    r"\b(are you|is this)\s+(chatgpt|openai|meta(\s*ai)?|llama|claude|gemini|bard)\b"
    r"|\b(chatgpt|openai|meta\s*ai|llama)\b",
    re.IGNORECASE,
)


def resolve_identity_reply(message: str) -> str | None:
    """Return canonical SereneMind identity text for identity / origin questions."""
    text = (message or "").strip()
    if not text:
        return None

    if _IDENTITY_CREATOR_RE.search(text):
        if re.search(r"\b(company|organization|meta|openai)\b", text, re.IGNORECASE):
            return (
                "I'm not developed by Meta, OpenAI, or any commercial AI company. "
                f"{IDENTITY_CREATOR}"
            )
        return IDENTITY_CREATOR

    if re.search(r"\b(are you|is this)\s+(chatgpt|openai|meta(\s*ai)?|llama|claude|gemini|bard)\b", text, re.IGNORECASE):
        return IDENTITY_DENY_EXTERNAL

    if _IDENTITY_WHO_RE.search(text):
        return IDENTITY_INTRO

    if _IDENTITY_EXTERNAL_RE.search(text) and re.search(
        r"\b(who|what|which|company|developed|created|made|built)\b", text, re.IGNORECASE
    ):
        return (
            "I'm not developed by Meta, OpenAI, or any commercial AI company. "
            f"{IDENTITY_CREATOR}"
        )

    return None


BASE_SYSTEM = f"{IDENTITY_CONSTRAINT} {CONVERSATION_STYLE}"

MEMORY_SYSTEM_ADDON = (
    " Verified memories may appear below. Use them only as optional context. "
    "Mention a remembered fact only when it clearly relates to the user's latest message "
    "(same topic: sport, hobby, cooking, exams, person, goal, preference, etc.). "
    "When relevant, weave one specific detail naturally into the reply — for example, "
    "if they watch cricket and a favourite player is listed, name that player; "
    "if they cook and cooking is listed, connect to that interest; "
    "if they feel stressed and exams/goals are listed, gently check whether that is related. "
    "If nothing in the list meaningfully fits the latest message, ignore all memories and reply normally. "
    "Do not force memories into unrelated chat. "
    "Do not repeat the same remembered fact if you already mentioned it in a recent assistant turn. "
    "Use at most one memory detail per reply. Never invent names, hobbies, teams, or past events."
)

MEMORY_RECALL_SYSTEM = (
    f"{IDENTITY_CONSTRAINT} "
    "The user is asking what you remember about them. "
    "Answer using ONLY the verified memories listed below. "
    "Include their name, hobbies, sports, favourite team/player, and any emotional context if present. "
    "Summarize naturally in 2-4 short sentences. Never fabricate details. "
    "If a category is missing from the list, do not guess. Do not ask a counselling follow-up."
)

GREETING_SYSTEM = (
    f"{IDENTITY_CONSTRAINT} "
    "The user sent a greeting. Reply warmly in 1-2 short sentences. "
    "Sound casual and human — a simple hello, not a therapy intake. "
    "Do NOT say 'I'm SereneMind' or describe your purpose. "
    "Do NOT reference past conversations or memories unless the user mentions them now. "
    "A light open invitation is fine; avoid stock counselling questions."
)

SMALL_TALK_SYSTEM = (
    f"{IDENTITY_CONSTRAINT} "
    "This is casual conversation. Keep it light, natural, and brief (1-3 short sentences). "
    "Match the user's energy. Chat about the topic they raised. "
    "Do NOT introduce yourself or mention your developer. "
    "Do NOT reference past conversations unless the user mentions them now. "
    "At most one light question — or none if a simple reply is enough."
)

EMOTIONAL_SHARE_SYSTEM = (
    f"{BASE_SYSTEM} "
    "Respond to the feeling in the latest message — do not mix in unrelated earlier topics. "
    "If a Verified memory clearly relates to this feeling or topic (e.g. exams when stressed, "
    "a hobby when they mention that activity), you may gently connect to that one fact; "
    "otherwise stay only with what they just said. "
    "Use Current analysis (emotion, mental_state, tags) to choose tone: "
    "joy / excitement / achievement / pride / success → celebrate the specific win warmly; "
    "share the moment; do not dig for hidden problems or ask how it 'makes them feel'. "
    "hobbies / interests / fun plans → be curious and engaged; use a related remembered preference if listed. "
    "sadness / loneliness → validate gently and specifically; quiet presence over probing; "
    "do not pivot to past achievements to 'cheer them up' unless they mention those. "
    "stress / anxiety / overwhelm → acknowledge the pressure; if a related goal/exam memory is listed, "
    "you may gently ask whether today's stress connects to that. "
    "grief / loss → be soft and respectful; do not rush them. "
    "anger / frustration → acknowledge the frustration without lecturing. "
    "Match intensity — do not oversell positivity or cheerlead. "
    "Reflect a concrete detail from their latest words before any question. "
    "Prefer a reflective statement with no question when their share already feels complete. "
    "Use Current analysis only for tone; do not repeat clinical labels like 'low mood', "
    "'hopelessness', or severity scores back to the user — speak in plain, human language."
)

CRISIS_SYSTEM = (
    f"{IDENTITY_CONSTRAINT} "
    "Crisis mode: stay calm, grounded, and brief. "
    "Acknowledge they are in serious distress without interrogating. "
    "Include Umang Mental Health Helpline 0317-4288665 (24/7). "
    "Encourage reaching out to someone they trust. "
    "Do not use casual banter, celebration, or identity self-intro. "
    "Do not ask multiple questions."
)

SYSTEM_PROMPTS = {
    "default": BASE_SYSTEM,
    "greeting": GREETING_SYSTEM,
    "small_talk": SMALL_TALK_SYSTEM,
    "factual": BASE_SYSTEM + " Answer directly and briefly. Prefer a clear answer over a follow-up question.",
    "memory_recall": MEMORY_RECALL_SYSTEM,
    "emotional_share": EMOTIONAL_SHARE_SYSTEM,
    "crisis": CRISIS_SYSTEM,
}

FRESH_INTENTS = frozenset({"greeting", "small_talk"})
MAX_HISTORY_TURN_CHARS = 220
MAX_MEMORY_SNIPPET_CHARS = 160


def _truncate(text: str | None, limit: int) -> str:
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _format_memories_compact(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return ""
    parts = []
    seen: set[str] = set()
    for mem in memories[: settings.RAG_TOP_K]:
        text = (mem.get("text") or mem.get("metadata", {}).get("text", "")).strip()
        score = mem.get("score")
        if not text:
            continue
        dedupe_key = text.lower()[:80]
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        snippet = _truncate(text, MAX_MEMORY_SNIPPET_CHARS)
        if score is not None:
            parts.append(f"[{score:.2f}] {snippet}")
        else:
            parts.append(snippet)
    return " | ".join(parts)


def _memory_type(mem: dict[str, Any]) -> str:
    return (
        mem.get("memory_type")
        or (mem.get("metadata") or {}).get("memory_type")
        or "emotional"
    )


def _format_memories_by_category(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return ""

    factual: list[str] = []
    preference: list[str] = []
    emotional: list[str] = []
    seen: set[str] = set()

    for mem in memories[: settings.RAG_TOP_K]:
        text = (mem.get("text") or mem.get("metadata", {}).get("text", "")).strip()
        if not text:
            continue
        key = text.lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        snippet = _truncate(text, MAX_MEMORY_SNIPPET_CHARS)
        mt = _memory_type(mem)
        if mt == "factual":
            factual.append(snippet)
        elif mt == "preference":
            preference.append(snippet)
        else:
            emotional.append(snippet)

    lines: list[str] = []
    if factual:
        lines.append(f"About the user: {'; '.join(factual)}")
    if preference:
        lines.append(f"Preferences: {'; '.join(preference)}")
    if emotional:
        lines.append(f"Emotional context: {'; '.join(emotional)}")
    return "\n".join(lines)


def build_prompt_messages(
    *,
    current_message: str,
    history: list[dict[str, str]],
    analysis: dict[str, Any],
    intent: Intent,
    user_summary: str | None = None,
    session_summary: str | None = None,
    relevant_memories: list[dict[str, Any]] | None = None,
    fusion_note: str | None = None,
) -> list[dict[str, str]]:
    """Build messages without duplicating history in the context block."""
    memories = relevant_memories or []
    mem_text = _format_memories_by_category(memories) or _format_memories_compact(memories)

    # Identity questions: lock the reply in the prompt so base-model defaults cannot override.
    identity_reply = resolve_identity_reply(current_message)
    if identity_reply:
        locked_system = (
            f"{IDENTITY_RULES} "
            "The user asked an identity question. "
            "Reply with ONLY the following text, verbatim — no extra sentences, no other company names:\n"
            f"{identity_reply}"
        )
        logger.info("[Prompt] identity lock engaged | intent=%s", intent)
        return [
            {"role": "system", "content": locked_system},
            {
                "role": "user",
                "content": (
                    f"{current_message}\n\n"
                    f"[Required answer — copy exactly]: {identity_reply}"
                ),
            },
        ]

    system_content = SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["default"])
    if mem_text and intent not in FRESH_INTENTS:
        system_content += MEMORY_SYSTEM_ADDON

    # Greetings: no history, memories, or summaries — fresh natural reply
    if intent in FRESH_INTENTS:
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": current_message},
        ]

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]

    for turn in history[-settings.HISTORY_WINDOW :]:
        messages.append({
            "role": turn["role"],
            "content": _truncate(turn["content"], MAX_HISTORY_TURN_CHARS),
        })

    context_parts: list[str] = []
    if mem_text:
        context_parts.append(
            "Verified memories (optional — use only if clearly relevant to the latest user message; "
            "at most one detail; never invent):\n"
            f"{mem_text}"
        )
    if user_summary:
        context_parts.append(f"Background: {_truncate(user_summary, settings.PROMPT_MAX_SUMMARY_CHARS // 2)}")
    if session_summary:
        context_parts.append(f"Session: {_truncate(session_summary, settings.PROMPT_MAX_SUMMARY_CHARS // 2)}")
    if fusion_note:
        context_parts.append(fusion_note)
    if intent in ("emotional_share", "crisis", "memory_recall") or mem_text:
        context_parts.append(
            f"Current analysis: emotion={analysis.get('emotion', 'neutral')}, "
            f"mental_state={analysis.get('mental_state', 'normal')}, "
            f"severity={analysis.get('severity_rating', 0)}, "
            f"assessment={_truncate(analysis.get('semantic_summary', ''), 180)}, "
            f"tags={', '.join(analysis.get('tags') or [])}, "
            f"crisis={analysis.get('crisis_risk', 'LOW')}"
        )

    user_content = current_message
    if context_parts:
        user_content = "\n".join(context_parts) + f"\n\nUser: {current_message}"

    messages.append({"role": "user", "content": user_content})

    prompt_chars = sum(len(m["content"]) for m in messages)
    logger.info(
        "[Prompt] intent=%s | memories=%d | fusion=%s | chars=%d",
        intent,
        len(memories),
        bool(fusion_note),
        prompt_chars,
    )

    return messages


GREETING_REPLIES = [
    "Hey — good to see you. How's your day going?",
    "Hi there. I'm glad you stopped by.",
    "Hello. Hope you're doing alright today.",
    "Hey. What's been keeping you busy?",
]

SMALL_TALK_REPLIES = [
    "Got it — I'm with you.",
    "Nice. I'm listening whenever you want to keep going.",
    "Sounds good. What else is on your mind?",
    "Alright. I'm here.",
]

POSITIVE_REPLIES = [
    "That's wonderful — you should feel proud of that.",
    "Love that for you. Sounds like a real win.",
    "That's exciting. Glad things lined up for you.",
]

EMOTIONAL_REPLIES = [
    "That sounds heavy. I'm here with you.",
    "I hear you — that would weigh on anyone.",
    "Thanks for sharing that. You don't have to carry it alone here.",
    "That makes sense. It's okay to feel this way.",
]

CRISIS_REPLIES = [
    "Please call Umang Mental Health Helpline at 0317-4288665 (24/7). You don't have to handle this alone.",
    "Reach out to someone you trust, or call Umang at 0317-4288665 — available around the clock.",
]

_POSITIVE_EMOTIONS = frozenset({
    "joy", "happy", "happiness", "excited", "excitement", "pride", "proud",
    "relief", "grateful", "gratitude", "content", "hopeful",
})


def fallback_reply(intent: Intent, analysis: dict[str, Any], message: str | None = None) -> str:
    import random

    identity = resolve_identity_reply(message or "")
    if identity:
        return identity

    if intent == "greeting":
        return random.choice(GREETING_REPLIES)
    if intent == "small_talk":
        return random.choice(SMALL_TALK_REPLIES)
    if intent == "crisis":
        return random.choice(CRISIS_REPLIES)
    if intent == "emotional_share":
        emotion = str((analysis or {}).get("emotion") or "").lower()
        tags = " ".join(analysis.get("tags") or []).lower() if analysis else ""
        if emotion in _POSITIVE_EMOTIONS or any(
            k in tags for k in ("joy", "pride", "achievement", "success", "excited")
        ):
            return random.choice(POSITIVE_REPLIES)
        return random.choice(EMOTIONAL_REPLIES)
    return random.choice(GREETING_REPLIES)
