import re
from typing import Literal

from app.crisis_rules import check_rule_based_crisis
from app.services.memory_retrieval import is_memory_recall_query

Intent = Literal["greeting", "small_talk", "emotional_share", "crisis", "factual", "memory_recall"]

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

# Phase P0.5-B — neutral declarative statements (identity, project, study, preference, work).
# Matched only after distress, crisis, recall, and greeting checks so mixed messages stay emotional.
FACTUAL_DECLARATIVE_PATTERNS = [
    r"^my name is\b",
    r"^i am\b",
    r"^i'm\b",
    r"^im\b",
    r"^my (project|final year|fyp|favourite|favorite|degree|university|uni|team|job|work|hobby|passion)\b",
    r"^i (study|studied|work|working|love|like|enjoy|prefer|build|building|develop|developing|create|creating|make|making)\b",
    r"\bmy (project|final year project|fyp) (is|was|called|named)\b",
    r"\bi am a\b",
    r"\bi'm a\b",
    r"\bi am (studying|working on|building|developing|creating|making)\b",
    r"\bi'm (studying|working on|building|developing|creating|making)\b",
    r"\bi study\b",
    r"\bi'?m working on\b",
    r"\bmy favourite\b",
    r"\bmy favorite\b",
    r"\bfocuses on\b",
    r"\bprovides\b",
    r"\baims to\b",
    r"\bis designed to\b",
    r"\boffers\b",
]


def is_factual_declarative(message: str) -> bool:
    """True when the message reads as a neutral factual/preference statement."""
    text = (message or "").strip()
    if not text:
        return False
    if is_memory_recall_query(message):
        return False
    lower = text.lower()
    return any(re.search(pattern, lower, re.IGNORECASE) for pattern in FACTUAL_DECLARATIVE_PATTERNS)


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

    if is_memory_recall_query(message):
        return "memory_recall"

    for pattern in SMALL_TALK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "small_talk"

    if "?" in text and len(text.split()) <= 12:
        return "factual"

    if len(text.split()) <= 3 and text in ("thanks", "thank you", "ok", "okay", "yes", "no", "sure"):
        return "small_talk"

    # Phase P0.5-B: pattern-based factual routing (not length-based emotional_share default).
    if is_factual_declarative(message):
        return "factual"

    return "small_talk"
