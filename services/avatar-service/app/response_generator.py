"""
Smart ML-driven response generator for SereneMind Avatar.

This module constructs empathetic, contextual responses dynamically
using the outputs of all three trained ML models:
  1. Emotion Classifier       (emotion label + confidence)
  2. Crisis Detector          (crisis_probability 0-1 + risk_level)
  3. Mental Health Classifier (mental_state label + confidence)

No OpenAI key required — responses are built from model outputs.
If an OpenAI key IS present, it uses GPT-4o-mini for richer, generative text.
"""

import os
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.warning("openai package not installed — ML-driven template engine will be used.")

# ---------------------------------------------------------------------------
# EMOTION TEMPLATES — Multiple variants per emotion so responses feel natural
# Placeholders:  {emotion}, {conf_pct}, {mental_state}, {risk_level}
# ---------------------------------------------------------------------------
EMOTION_OPENERS = {
    "joy": [
        "There's a warmth in your words that's really uplifting to sense ✨.",
        "It sounds like something genuinely good happened for you today 🌟.",
        "Joy is worth capturing — you're already doing something powerful by naming it.",
    ],
    "sadness": [
        "Sadness takes real courage to put into words, and you've done that.",
        "The weight you're carrying right now sounds heavy. You don't have to face it alone.",
        "Thank you for trusting this space with something so tender.",
    ],
    "anger": [
        "Your frustration makes complete sense — anger is often a signal that something important was crossed.",
        "It takes self-awareness to recognise and name anger, and you've done exactly that.",
        "What you're feeling is valid. Anger is information, not a flaw.",
    ],
    "fear": [
        "Feeling afraid is deeply human, and you are safe to express it here.",
        "Fear can narrow the world down to a pinpoint. What you're feeling is real and valid.",
        "Naming a fear is often the first step toward loosening its hold on you.",
    ],
    "love": [
        "There's something beautiful in what you've shared — connection is one of our deepest needs.",
        "Love and care for others (or ourselves) deserves to be acknowledged.",
        "It's meaningful that you're sharing something so personal.",
    ],
    "surprise": [
        "Life can throw unexpected twists, and it sounds like you're still processing this one.",
        "Surprise — whether pleasant or unsettling — deserves a moment to sit with.",
        "Unexpected moments can shake our footing. How are you feeling about it now?",
    ],
    "disgust": [
        "Something is clearly sitting wrong with you, and your gut reaction matters.",
        "It's worth listening to what that discomfort is telling you.",
        "Discomfort and disgust often point to values that feel violated — that's worth exploring.",
    ],
    "neutral": [
        "Thank you for sharing with me today — even moments that feel ordinary deserve space.",
        "Sometimes it's hard to put a name to exactly how we feel, and that's okay.",
        "You showed up and wrote something down, and that matters more than you might think.",
    ],
}

# ---------------------------------------------------------------------------
# MENTAL-STATE BRIDGES — contextualised commentary from the mental health model
# ---------------------------------------------------------------------------
MENTAL_STATE_BRIDGES = {
    "anxiety": [
        "Our emotional analysis detected strong signs of anxiety ({conf_pct}% certainty) in what you shared.",
        "The patterns in your words suggest you may be experiencing heightened anxiety right now.",
        "What you described carries the unmistakable weight of anxiety — racing thoughts, worry, uncertainty.",
    ],
    "depression":  [
        "The emotional tone your words carry suggests this may connect to low mood or depression.",
        "Our analysis picked up indicators of low mood ({conf_pct}% confidence) — something worth being gentle with yourself about.",
        "Depression can make the smallest things feel impossible. What you're experiencing is real.",
    ],
    "depressive state": [
        "There's a heaviness in what you've written that our models associate with a depressive period.",
        "The pattern in your words suggests you may be going through a difficult emotional patch right now.",
        "These feelings of low mood are acknowledged — and they are real.",
    ],
    "stress": [
        "Your text shows clear signs of stress and cognitive overload.",
        "The analysis detected high stress markers ({conf_pct}% confidence) — your mind and body are telling you something.",
        "What you're describing sounds exhausting, and the stress your carrying is legitimate.",
    ],
    "normal": [
        "Your overall emotional baseline seems relatively balanced right now.",
        "The mental health analysis didn't detect any acute distress patterns — which is positive.",
        "",  # Can be empty — no forced commentary needed when all is well
    ],
    "ptsd": [
        "What you've described shows patterns that can be associated with trauma responses.",
        "Old wounds don't always stay in the past — and your experience of them is valid.",
        "",
    ],
    "bipolar": [
        "Our models detected some emotional intensity that can sometimes accompany mood fluctuations.",
        "",
        "",
    ],
}

# ---------------------------------------------------------------------------
# CLOSING QUESTIONS — encourage continued reflection
# ---------------------------------------------------------------------------
CLOSING_QUESTIONS = {
    "joy": [
        "What made today feel good — and is there a way to bring more of that in?",
        "How can you carry a little of this forward into tomorrow?",
        "What do you want to remember about this moment?",
    ],
    "sadness": [
        "What do you most need right now — space to feel this, or some gentle distraction?",
        "Is there someone in your life you feel safe talking to about this?",
        "What small act of kindness could you offer yourself today?",
    ],
    "anger": [
        "What would need to change for this to feel more manageable?",
        "Is there an action you can take that would help you feel heard?",
        "What's the thing underneath the anger that you most want acknowledged?",
    ],
    "fear": [
        "What's the worst that could happen — and could you survive it?",
        "What's one very small thing that could help you feel a little safer right now?",
        "Has there been a time before when fear felt this strong, and you got through it?",
    ],
    "love": [
        "How does that connection make you feel about yourself?",
        "What do you most want to nurture in this relationship?",
        "",
    ],
    "surprise": [
        "Now that the dust has settled a little, how are you truly feeling about it?",
        "Was this more welcome or unsettling — or both?",
        "",
    ],
    "neutral": [
        "Is there something beneath the surface worth exploring today?",
        "What's one thing you genuinely felt today, even if it was small?",
        "",
    ],
    "disgust": [
        "What value of yours do you feel was disrespected here?",
        "",
        "",
    ],
}

# ---------------------------------------------------------------------------
# CRISIS ADDITIONS — appended when risk is elevated
# ---------------------------------------------------------------------------
CRISIS_ADDS = {
    "MEDIUM": "If things start to feel more overwhelming, please don't hesitate to reach out to someone you trust.",
    "HIGH": "I want you to know that what you're feeling matters — and so do you. Please consider reaching out to Umang (0317-4288665), a confidential mental health helpline available in Pakistan.",
    "CRISIS": "🆘 I'm genuinely concerned about your safety right now. Please reach out immediately — Umang helpline: 0317-4288665. You matter deeply, and support is available right now.",
}

# CONFIDENCE threshold labels
def _conf_label(conf: float) -> str:
    if conf >= 0.85: return "high"
    if conf >= 0.60: return "moderate"
    return "mild"


def _build_smart_response(
    emotion: str,
    confidence: float,
    risk_level: str,
    crisis_probability: float,
    mental_state: str,
    mental_health_confidence: float,
) -> str:
    """
    Build a dynamic, contextual response purely from ML model outputs.
    Uses weighted random selection across template pools to avoid repetition.
    """
    emotion_key = emotion.lower()
    mental_key = mental_state.lower()
    conf_pct = int(confidence * 100)
    mh_pct = int(mental_health_confidence * 100)
    conf_word = _conf_label(confidence)

    # 1. Opening — emotion-driven
    openers = EMOTION_OPENERS.get(emotion_key, EMOTION_OPENERS["neutral"])
    opener = random.choice(openers)

    # 2. Confidence context — tell user what the model detected
    if confidence >= 0.70:
        conf_line = f"Our emotion model detected **{emotion_key}** with {conf_word} confidence ({conf_pct}%)."
    else:
        conf_line = f"Your words carry undertones of {emotion_key} ({conf_pct}% confidence from our model), though emotions are rarely one thing."

    # 3. Mental health bridge — insight from the mental health classifier
    mh_options = MENTAL_STATE_BRIDGES.get(mental_key, MENTAL_STATE_BRIDGES["normal"])
    mh_bridge = random.choice([m for m in mh_options if m])  # skip empty options
    if mh_bridge:
        mh_bridge = mh_bridge.replace("{conf_pct}", str(mh_pct))

    # 4. Crisis awareness
    if crisis_probability >= 0.80:
        crisis_line = f"I want to pause and check in — our crisis analysis detected significant distress signals ({int(crisis_probability*100)}% probability). Please know you are not alone."
    elif crisis_probability >= 0.50:
        crisis_line = f"There are signs of distress in what you wrote ({int(crisis_probability*100)}%). This is worth paying attention to."
    else:
        crisis_line = ""

    # 5. Closing question — emotion-driven, encourages reflection
    closing_opts = CLOSING_QUESTIONS.get(emotion_key, CLOSING_QUESTIONS["neutral"])
    closing = random.choice([c for c in closing_opts if c]) if any(closing_opts) else ""

    # 6. Crisis resource if needed
    crisis_add = CRISIS_ADDS.get(risk_level, "")

    # --- Assemble ---
    parts = [opener, conf_line]
    if mh_bridge:
        parts.append(mh_bridge)
    if crisis_line:
        parts.append(crisis_line)
    if closing:
        parts.append(closing)
    if crisis_add:
        parts.append(crisis_add)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# GPT SYSTEM PROMPT — used when OpenAI key is available
# ---------------------------------------------------------------------------
GPT_SYSTEM_PROMPT = """You are SereneMind, a warm and empathetic AI mental health companion.
You are NOT a licensed therapist. Always recommend professional help for serious issues.

PERSONALITY: Warm, gentle, non-judgmental. Validates feelings before offering perspective.
RESPONSE FORMAT: 3-5 sentences. Acknowledge emotion first. End with an open question.
SAFETY: If risk_level is HIGH or CRISIS, include Umang 0317-4288665. Never minimise feelings.
"""


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------
def generate_avatar_response(
    journal_text: str,
    emotion: str,
    confidence: float,
    risk_level: str,
    crisis_probability: float = 0.0,
    mental_state: str = "normal",
    mental_health_confidence: float = 0.0,
    conversation_history: Optional[list] = None,
) -> dict:
    """
    Generate a contextual avatar response using:
    - All 3 ML model outputs as primary inputs
    - GPT-4o-mini if OPENAI_API_KEY is set, otherwise the smart template engine
    """

    # Try GPT-4o-mini first if key is available
    if client:
        try:
            messages = [{"role": "system", "content": GPT_SYSTEM_PROMPT}]
            if conversation_history:
                messages.extend(conversation_history[-6:])

            user_msg = (
                f'Journal: "{journal_text}"\n'
                f'Emotion Model → {emotion} ({confidence*100:.1f}%)\n'
                f'Crisis Model  → {risk_level} (p={crisis_probability:.2f})\n'
                f'Mental Health → {mental_state} ({mental_health_confidence*100:.1f}%)\n'
                f'{"CRITICAL: Include Umang 0317-4288665" if risk_level in ["HIGH","CRISIS"] else ""}'
            )
            messages.append({"role": "user", "content": user_msg})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=220,
                temperature=0.72,
            )
            avatar_text = response.choices[0].message.content.strip()
            return {
                "text": avatar_text,
                "emotion_context": emotion,
                "mental_state": mental_state,
                "risk_acknowledged": risk_level in ["HIGH", "CRISIS"],
                "source": "gpt-4o-mini",
                "tokens_used": response.usage.total_tokens,
            }
        except Exception as e:
            logger.error(f"GPT call failed: {e}. Falling back to ML-driven templates.")

    # --- ML-DRIVEN TEMPLATE ENGINE (no API key needed) ---
    avatar_text = _build_smart_response(
        emotion=emotion,
        confidence=confidence,
        risk_level=risk_level,
        crisis_probability=crisis_probability,
        mental_state=mental_state,
        mental_health_confidence=mental_health_confidence,
    )

    logger.info(
        f"ML-driven response | emotion={emotion}({confidence:.2f}) | "
        f"mental={mental_state}({mental_health_confidence:.2f}) | risk={risk_level}({crisis_probability:.2f})"
    )

    return {
        "text": avatar_text,
        "emotion_context": emotion,
        "mental_state": mental_state,
        "risk_acknowledged": risk_level in ["HIGH", "CRISIS"],
        "source": "ml-template",
        "tokens_used": 0,
    }
