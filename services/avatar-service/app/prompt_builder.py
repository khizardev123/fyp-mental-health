"""Compact prompt builder — optimized for low token count and latency."""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

from app.core.config import settings

logger = logging.getLogger(__name__)

Intent = str
TurnMode = Literal["listen", "reflect", "ask", "support"]
CrisisProfile = Literal[
    "suicidal_ideation", "hopelessness", "panic", "grief", "loneliness", "acute_distress"
]

PROMPT_MEMORY_MAX = 2

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

IDENTITY_CONSTRAINT = (
    "You are SereneMind, a supportive conversational companion. "
    "Never claim to be ChatGPT, OpenAI, Meta AI, Llama, Claude, Gemini, or any other AI product or company. "
    "Do NOT introduce yourself, say 'I'm SereneMind', or mention your developer unless the user "
    "explicitly asks who/what you are, who created you, or whether you are another AI."
)

SERENEMIND_PERSONALITY = (
    "You are a calm, emotionally intelligent companion — warm, patient, and curious, "
    "not a generic chatbot or clinical counselor. "
    "Sound like a thoughtful friend who listens carefully. "
    "Default flow: observe something specific they said → reflect it briefly → "
    "optional single question only when it opens space (never stack questions). "
    "Use 2-4 short sentences in plain spoken language. "
    "Vary wording every turn; do not repeat your last opener or closing. "
    "Curiosity before advice — do not lecture, diagnose, or list steps unless they ask. "
    "When goals, studies, relationships, or hobbies come up, connect naturally to their words. "
    "If they change topic, follow the new topic only. "
    "Never use pet names. You are not a licensed therapist. "
    "Do not use stock phrases such as: \"I'm here for you\", \"It's okay to feel this way\", "
    "\"Your feelings are valid\", \"Thank you for sharing\", \"That must be hard\", "
    "\"It's understandable\", \"Tell me more\", \"Can you elaborate\", "
    "\"How does that make you feel\", or near-paraphrases. "
    "If crisis signals appear, stay calm and include Umang Mental Health Helpline 0317-4288665 (24/7)."
)

# Backward-compatible alias
CONVERSATION_STYLE = SERENEMIND_PERSONALITY

BASE_SYSTEM = f"{IDENTITY_CONSTRAINT} {SERENEMIND_PERSONALITY}"

MEMORY_SYSTEM_ADDON = (
    " Verified memories may appear below. Use ONLY those facts — never invent names, events, or history. "
    "Weave at most one memory detail naturally when it clearly fits their latest message. "
    "Prefer journey phrasing (\"Last time you mentioned the FYP — how's it going?\") "
    "over listing facts. If nothing fits, ignore all memories."
)

_GREETING_OVERLAY = (
    "The user sent a greeting. Reply in 1-2 warm, casual sentences. "
    "Do not reference past conversations unless they mention them now."
)

_SMALL_TALK_OVERLAY = (
    "Casual conversation — match their energy in 1-3 sentences. "
    "Respond to the specific thing they raised."
)

_EMOTIONAL_OVERLAY = (
    "The user is sharing something emotional. Reflect a concrete detail before any question. "
    "Match their intensity — no cheerleading or forced positivity. "
    "Joy or achievement → celebrate the specific win. "
    "Grief or loss → soft and unhurried. "
    "Stress or anxiety → name the pressure, explore what feels heaviest if one question fits. "
    "Use tone guidance below for intensity only — never repeat clinical labels to the user."
)

_FACTUAL_OVERLAY = (
    "Answer directly in 2-3 sentences. Weave one memory detail only if it clearly helps."
)

_MEMORY_RECALL_OVERLAY = (
    "The user asks what you remember. Answer in warm conversational prose (2-4 sentences) — "
    "as if recalling a friend, not a profile or database. "
    "Use at most two memory details from the list. Never invent. Do not use category headers."
)

CRISIS_SYSTEM_BASE = (
    f"{IDENTITY_CONSTRAINT} "
    "The user is in significant distress. Stay calm, grounded, and human — not clinical. "
    "In 3-5 short sentences, naturally include ALL of the following: "
    "(1) reflect something specific they said in plain words; "
    "(2) thank them briefly for trusting you with something this heavy; "
    "(3) exactly ONE gentle safety question suited to their words; "
    "(4) encourage someone they trust now, and emergency services if immediate danger; "
    "(5) offer to stay here with them in this chat; "
    "(6) Umang Mental Health Helpline 0317-4288665 (24/7). "
    "Do not use therapy clichés, numbered steps, or clinical labels. "
    "Do not ask more than one question. No casual banter or self-introduction."
)

CRISIS_SITUATION_GUIDANCE: dict[CrisisProfile, str] = {
    "suicidal_ideation": (
        "Situation: suicidal thoughts or self-harm. Calm and direct. "
        "Safety question example: \"Are you safe right now, or do you feel you might hurt yourself?\""
    ),
    "hopelessness": (
        "Situation: hopelessness or giving up. Quiet steadiness — do not argue them into hope. "
        "Safety question example: \"Right now, do you feel mostly exhausted, or like you might act on these thoughts?\""
    ),
    "panic": (
        "Situation: panic or acute anxiety (racing heart, can't breathe). "
        "Validate the physical fear — short sentences. "
        "Safety question example: \"Are you somewhere you can sit down safely for a minute?\""
    ),
    "grief": (
        "Situation: grief or bereavement. Honor the loss — no silver linings. "
        "Safety question example: \"Is it the missing them that's hardest tonight, or feeling alone with it?\""
    ),
    "loneliness": (
        "Situation: loneliness or feeling unseen. Warm presence — do not say \"just reach out.\" "
        "Safety question example: \"Is there one person who might answer if you reached out tonight?\""
    ),
    "acute_distress": (
        "Situation: acute distress. Reflect their exact words. "
        "One safety question about whether they feel safe or might hurt themselves."
    ),
}

TURN_MODE_GUIDANCE: dict[TurnMode, str] = {
    "listen": (
        "Turn mode: listen — short acknowledgment only; no question this turn."
    ),
    "reflect": (
        "Turn mode: reflect — mirror a specific detail they shared; no question unless essential."
    ),
    "ask": (
        "Turn mode: ask — one thoughtful question tied to their words; nothing generic."
    ),
    "support": (
        "Turn mode: support — encourage or celebrate a concrete detail; at most one gentle question."
    ),
}

SYSTEM_PROMPTS = {
    "default": BASE_SYSTEM,
    "greeting": f"{BASE_SYSTEM} {_GREETING_OVERLAY}",
    "small_talk": f"{BASE_SYSTEM} {_SMALL_TALK_OVERLAY}",
    "factual": f"{BASE_SYSTEM} {_FACTUAL_OVERLAY}",
    "memory_recall": f"{BASE_SYSTEM} {_MEMORY_RECALL_OVERLAY}",
    "emotional_share": f"{BASE_SYSTEM} {_EMOTIONAL_OVERLAY}",
    "crisis": CRISIS_SYSTEM_BASE,
}

FRESH_INTENTS = frozenset({"greeting", "small_talk"})
MAX_HISTORY_TURN_CHARS = 220
MAX_MEMORY_SNIPPET_CHARS = 160

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

_SELF_HARM_RE = re.compile(
    r"\b(suicid|kill myself|end my life|want to die|hurt myself|self[- ]?harm|cut myself)\b",
    re.I,
)
_PANIC_RE = re.compile(
    r"\b(panic attack|panicking|can't breathe|cannot breathe|heart racing|heart is racing)\b",
    re.I,
)
_GRIEF_RE = re.compile(
    r"\b(grief|grieving|mourning|passed away|funeral|died|death of|lost my)\b",
    re.I,
)
_LONELY_RE = re.compile(
    r"\b(lonely|loneliness|nobody cares|no one cares|isolated|isolation|feel alone)\b",
    re.I,
)
_HOPELESS_RE = re.compile(
    r"\b(hopeless|give up|can't do this|cannot do this|can't go on|nothing matters)\b",
    re.I,
)

_POSITIVE_EMOTIONS = frozenset({
    "joy", "happy", "happiness", "excited", "excitement", "pride", "proud",
    "relief", "grateful", "gratitude", "content", "hopeful",
})


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

    if re.search(
        r"\b(are you|is this)\s+(chatgpt|openai|meta(\s*ai)?|llama|claude|gemini|bard)\b",
        text,
        re.IGNORECASE,
    ):
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


def infer_crisis_profile(message: str, analysis: dict[str, Any]) -> CrisisProfile:
    """Read-only crisis wording profile for prompt generation — does not change detection."""
    text = (message or "").lower()
    tags = " ".join(analysis.get("tags") or []).lower()
    mental = (analysis.get("mental_state") or "").lower()

    if _SELF_HARM_RE.search(text):
        return "suicidal_ideation"
    if _PANIC_RE.search(text) or mental == "acute anxiety" or "panic" in tags:
        return "panic"
    if _GRIEF_RE.search(text) or "loss" in tags or analysis.get("raw_label") == "grief":
        return "grief"
    if _LONELY_RE.search(text) or "loneliness" in tags:
        return "loneliness"
    if _HOPELESS_RE.search(text) or analysis.get("crisis_risk") == "HIGH":
        return "hopelessness"
    return "acute_distress"


def build_crisis_system_prompt(message: str, analysis: dict[str, Any]) -> str:
    profile = infer_crisis_profile(message, analysis)
    guidance = CRISIS_SITUATION_GUIDANCE.get(profile, CRISIS_SITUATION_GUIDANCE["acute_distress"])
    return f"{CRISIS_SYSTEM_BASE} {guidance}"


def build_crisis_context_note(message: str, analysis: dict[str, Any]) -> str:
    profile = infer_crisis_profile(message, analysis)
    snippet = _truncate(message, 120)
    return (
        "[Crisis context — internal; do not repeat these labels to the user]\n"
        f"Profile: {profile.replace('_', ' ')}. They said: \"{snippet}\". "
        "Respond to their latest words first."
    )


def _assistant_asked_last(history: list[dict[str, str]]) -> bool:
    for turn in reversed(history):
        if turn.get("role") == "assistant":
            return "?" in (turn.get("content") or "")
    return False


def infer_turn_mode(
    *,
    intent: Intent,
    analysis: dict[str, Any],
    history: list[dict[str, str]],
    message: str,
) -> TurnMode:
    """Lightweight turn guidance from history — no persistence."""
    if intent == "crisis":
        return "support"
    if intent in FRESH_INTENTS:
        return "listen"

    emotion = str(analysis.get("emotion") or "").lower()
    tags = [t.lower() for t in (analysis.get("tags") or [])]
    words = len((message or "").split())
    asked_last = _assistant_asked_last(history)

    if emotion in _POSITIVE_EMOTIONS or any(t in tags for t in ("joy", "achievement", "pride")):
        return "support"

    if asked_last:
        return "listen" if words <= 10 else "reflect"

    if intent == "memory_recall":
        return "reflect"

    if analysis.get("raw_label") == "grief" or "loss" in tags:
        return "reflect"

    if words <= 6:
        return "listen"

    if intent == "emotional_share" and words >= 10 and not asked_last:
        return "ask"

    return "reflect"


def build_turn_guidance_note(mode: TurnMode) -> str:
    line = TURN_MODE_GUIDANCE.get(mode, TURN_MODE_GUIDANCE["reflect"])
    return f"[Conversation guidance — internal; do not mention to the user]\n{line}"


def _truncate(text: str | None, limit: int) -> str:
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _memory_text(mem: dict[str, Any]) -> str:
    return (mem.get("text") or mem.get("metadata", {}).get("text", "") or "").strip()


def _significant_tokens(text: str) -> set[str]:
    stop = frozenset({"i", "a", "the", "my", "is", "am", "and", "to", "it", "that", "you", "me"})
    return {w for w in re.findall(r"[a-z']+", text.lower()) if len(w) > 2 and w not in stop}


def _memories_surfaced_in_history(
    memories: list[dict[str, Any]],
    history: list[dict[str, str]],
) -> set[str]:
    """Keys of memory snippets already echoed in recent assistant turns."""
    surfaced: set[str] = set()
    assistant_text = " ".join(
        (t.get("content") or "").lower()
        for t in history
        if t.get("role") == "assistant"
    )
    if not assistant_text:
        return surfaced
    assistant_tokens = _significant_tokens(assistant_text)
    for mem in memories:
        text = _memory_text(mem).lower()
        if not text:
            continue
        key = text[:80]
        mem_tokens = _significant_tokens(text)
        if len(mem_tokens) < 2:
            continue
        overlap = mem_tokens & assistant_tokens
        if len(overlap) >= min(3, len(mem_tokens)):
            surfaced.add(key)
    return surfaced


def _format_memories_conversational(
    memories: list[dict[str, Any]],
    history: list[dict[str, str]] | None = None,
    *,
    max_items: int = PROMPT_MEMORY_MAX,
) -> str:
    """At most N memory snippets as plain lines — no category dumps."""
    if not memories:
        return ""

    history = history or []
    surfaced = _memories_surfaced_in_history(memories, history)
    lines: list[str] = []
    seen: set[str] = set()

    for mem in memories:
        text = _memory_text(mem)
        if not text:
            continue
        key = text.lower()[:80]
        if key in seen or key in surfaced:
            continue
        seen.add(key)
        lines.append(f"- {_truncate(text, MAX_MEMORY_SNIPPET_CHARS)}")
        if len(lines) >= max_items:
            break

    return "\n".join(lines)


def _format_memories_by_category(memories: list[dict[str, Any]]) -> str:
    """Legacy wrapper — delegates to conversational formatter."""
    return _format_memories_conversational(memories)


def _format_memories_compact(memories: list[dict[str, Any]]) -> str:
    return _format_memories_conversational(memories)


def _tone_guidance_note(analysis: dict[str, Any]) -> str:
    tags = ", ".join(analysis.get("tags") or []) or "none"
    return (
        "Tone guidance (internal — do not repeat labels to the user): "
        f"intensity={analysis.get('severity_rating', 0)}/10, "
        f"emotion={analysis.get('emotion', 'neutral')}, tags={tags}"
    )


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
    emotion_trajectory_note: str | None = None,
) -> list[dict[str, str]]:
    """Build messages without duplicating history in the context block."""
    memories = relevant_memories or []
    mem_text = _format_memories_conversational(memories, history)

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

    if intent == "crisis":
        system_content = build_crisis_system_prompt(current_message, analysis)
    else:
        system_content = SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["default"])

    if mem_text and intent not in FRESH_INTENTS:
        system_content += MEMORY_SYSTEM_ADDON

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
        if intent == "memory_recall":
            context_parts.append(
                "Verified memories (use ONLY these; conversational prose; never invent):\n"
                f"{mem_text}"
            )
        else:
            context_parts.append(
                "Verified memories (optional — at most one detail if clearly relevant; never invent):\n"
                f"{mem_text}"
            )

    if user_summary:
        context_parts.append(f"Background: {_truncate(user_summary, settings.PROMPT_MAX_SUMMARY_CHARS // 2)}")
    if session_summary:
        context_parts.append(f"Session: {_truncate(session_summary, settings.PROMPT_MAX_SUMMARY_CHARS // 2)}")
    if fusion_note:
        context_parts.append(fusion_note)
    if emotion_trajectory_note and intent not in FRESH_INTENTS and intent != "memory_recall":
        context_parts.append(emotion_trajectory_note)

    if intent == "crisis":
        context_parts.append(build_crisis_context_note(current_message, analysis))
    elif intent not in ("memory_recall",) and (
        intent == "emotional_share" or mem_text or emotion_trajectory_note
    ):
        context_parts.append(_tone_guidance_note(analysis))

    if intent not in ("crisis", "memory_recall"):
        turn_mode = infer_turn_mode(
            intent=intent,
            analysis=analysis,
            history=history,
            message=current_message,
        )
        context_parts.append(build_turn_guidance_note(turn_mode))

    user_content = current_message
    if context_parts:
        user_content = "\n".join(context_parts) + f"\n\nUser: {current_message}"

    messages.append({"role": "user", "content": user_content})

    logger.info(
        "[Prompt] intent=%s | memories=%d | chars=%d",
        intent,
        len(memories),
        sum(len(m["content"]) for m in messages),
    )

    return messages


GREETING_REPLIES = [
    "Hey — good to see you. What's been on your mind lately?",
    "Hi there. How's your day treating you so far?",
    "Hello. Anything you'd like to talk through today?",
    "Hey. What's been taking up most of your energy this week?",
]

SMALL_TALK_REPLIES = [
    "Ha — I hear you. What happened next?",
    "Nice. What's the best part of that for you?",
    "Got it. Is that something you've been looking forward to?",
    "Fair enough. What's drawing you to that?",
]

POSITIVE_REPLIES = [
    "That's a real win — what made it feel good for you?",
    "You sound proud of that. How did it all come together?",
    "That's exciting. What are you most looking forward to from here?",
]

EMOTIONAL_REPLIES = [
    "That sounds like a lot to carry. What's weighing on you most right now?",
    "I can hear how heavy that feels. Is it the situation itself, or everything around it?",
    "That would drain anyone. What part of this feels hardest today?",
    "Sounds like you've been holding a lot. Do you want to unpack it, or just sit with it for a moment?",
]

CRISIS_FALLBACK: dict[CrisisProfile, str] = {
    "suicidal_ideation": (
        "That sounds unbearably heavy. Thank you for saying it here — that takes trust. "
        "Are you safe right now, or do you feel you might hurt yourself? "
        "Please call Umang Mental Health Helpline at 0317-4288665 (24/7), reach someone you trust, "
        "or emergency services if you're in immediate danger. I'm here with you."
    ),
    "hopelessness": (
        "When everything feels hopeless, it can be exhausting just to get through the day. "
        "Thank you for telling me. Do you feel mostly worn down, or like you might act on these thoughts? "
        "Umang at 0317-4288665 (24/7) or someone you trust can sit with you — I'll stay here too."
    ),
    "panic": (
        "That racing heart and tight breath can feel terrifying. Thank you for reaching out in the middle of it. "
        "Are you somewhere you can sit down safely for a minute? "
        "Umang is 0317-4288665 (24/7) if you want a voice now — I'm not going anywhere."
    ),
    "grief": (
        "Grief can leave everything feeling hollow. Thank you for trusting me with something this tender. "
        "Is it the missing them that's hardest right now, or feeling alone with it? "
        "Umang at 0317-4288665 (24/7) or someone who knew them can be with you — I'm here too."
    ),
    "loneliness": (
        "Feeling unseen when you're hurting is its own kind of pain. Thank you for saying that here. "
        "Is there one person who might answer if you reached out tonight? "
        "Umang is 0317-4288665 (24/7) — and I'm still here in this chat with you."
    ),
    "acute_distress": (
        "I hear how much you're carrying right now. Thank you for telling me. "
        "Are you safe where you are, or do you feel you might hurt yourself? "
        "Please call Umang at 0317-4288665 (24/7) or someone you trust. I'm here with you."
    ),
}


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
        profile = infer_crisis_profile(message or "", analysis or {})
        return CRISIS_FALLBACK.get(profile, CRISIS_FALLBACK["acute_distress"])
    if intent == "emotional_share":
        emotion = str((analysis or {}).get("emotion") or "").lower()
        tags = " ".join(analysis.get("tags") or []).lower() if analysis else ""
        if emotion in _POSITIVE_EMOTIONS or any(
            k in tags for k in ("joy", "pride", "achievement", "success", "excited")
        ):
            return random.choice(POSITIVE_REPLIES)
        return random.choice(EMOTIONAL_REPLIES)
    return random.choice(GREETING_REPLIES)
