import re
from typing import Literal

from app.crisis_rules import check_rule_based_crisis

Intent = Literal["greeting", "small_talk", "emotional_share", "crisis", "factual", "memory_recall"]

RECALL_PATTERNS = [
    r"what do you remember",
    r"what do you know about me",
    r"what have i told you",
    r"what did i tell you",
    r"do you remember me",
    r"tell me what you remember",
    r"what do you recall",
    r"summarize what you know",
    r"everything you know about me",
]

GREETING_PATTERNS = [
    r"^(hi|hello|hey|hiya|howdy|good morning|good afternoon|good evening|good night)\b",
    r"^(hi|hello|hey)\s*[!?.]*$",
    r"^what'?s up\b",
    r"^how are you\b",
    # Self-introductions — must not be escalated to crisis on ML "i am <name>" false positives
    r"^(hi|hello|hey)[,!.]?\s*(there[,]?\s*)?(i am|i'm|im)\s+\w+",
    r"^(hi|hello|hey)[,!.]?\s*my name is\b",
    r"^my name is\b",
    r"^(hi|hello|hey)[,!.]?\s*(there[,]?\s*)?i am\s+\w+",
]

SMALL_TALK_PATTERNS = [
    r"\b(how are you|what'?s up|how'?s it going|how do you do|nice to meet)\b",
    r"\b(thank you|thanks|bye|goodbye|see you|talk later)\b",
    r"^(who are you|what are you|what can you do|tell me about yourself)\b",
    r"\?$",
]

EMOTIONAL_KEYWORDS = [
    "sad", "sadness", "depressed", "depression", "anxious", "anxiety", "stress", "stressed",
    "worried", "worry", "overwhelmed", "lonely", "loneliness", "angry", "anger", "frustrated",
    "frustration", "scared", "afraid", "fear", "hurt", "pain", "crying", "cry", "upset",
    "miserable", "hopeless", "exhausted", "tired of", "can't cope", "struggling",     "grief", "grieving", "heartbroken", "panic", "nervous", "tense", "burned out", "burnout",
    "feel bad", "feel awful", "feel terrible", "feel down", "not okay", "not ok", "breaking down",
    "not happy", "unhappy", "not good", "not great", "not fine",
]

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "want to die", "wish i was dead",
    "self harm", "self-harm", "hurt myself", "cut myself", "overdose", "no reason to live",
    "better off dead", "end it all", "take my life",
]


def detect_intent(message: str, ml_crisis_level: str | None = None) -> Intent:
    text = message.strip().lower()
    if not text:
        return "small_talk"

    for pattern in GREETING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "greeting"

    rule_level, _ = check_rule_based_crisis(message)
    if rule_level:
        return "crisis"

    for kw in CRISIS_KEYWORDS:
        if kw in text:
            return "crisis"

    if ml_crisis_level in ("HIGH", "CRISIS"):
        return "crisis"

    for kw in EMOTIONAL_KEYWORDS:
        if kw in text:
            return "emotional_share"

    for pattern in RECALL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "memory_recall"

    for pattern in SMALL_TALK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "small_talk"

    if "?" in text and len(text.split()) <= 12:
        return "factual"

    if len(text.split()) <= 3 and text in ("thanks", "thank you", "ok", "okay", "yes", "no", "sure"):
        return "small_talk"

    return "emotional_share" if len(text.split()) >= 8 else "small_talk"
