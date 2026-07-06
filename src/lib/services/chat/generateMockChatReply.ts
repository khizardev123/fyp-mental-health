import type { ChatGenerationInput, ChatGenerationResult } from "./types";

const MAX_REPLY_LEN = 2_000;

function clampReply(text: string): string {
  const t = text.trim();
  if (t.length <= MAX_REPLY_LEN) return t;
  return `${t.slice(0, MAX_REPLY_LEN - 1).trimEnd()}…`;
}

function normalizeEmotion(raw: string | null | undefined): string | null {
  if (!raw) return null;
  const s = raw.trim().toLowerCase();
  return s.length ? s : null;
}

/**
 * Rule-based supportive replies. Replace this function with a call to your
 * LLM provider while keeping {@link ChatGenerationInput} / {@link ChatGenerationResult}.
 */
export function generateMockChatReply(
  input: ChatGenerationInput,
): ChatGenerationResult {
  const msg = input.userMessage.trim();
  const emotion = normalizeEmotion(input.emotionContext.emotion);
  const hasJournalContinuity = input.journalContext.selectedEntries.length > 0;

  const keyword = (re: RegExp) => re.test(msg);

  let tonePrefix = "";
  if (emotion) {
    if (/(anxious|worried|nervous|panic|stress)/.test(emotion)) {
      tonePrefix =
        "I hear that things may feel intense right now. Let’s slow this down together. ";
    } else if (/(sad|down|depress|grief|lonely)/.test(emotion)) {
      tonePrefix =
        "Thank you for trusting me with this—it makes sense you’d feel heavy right now. ";
    } else if (/(angry|frustrat|irritat|mad)/.test(emotion)) {
      tonePrefix =
        "It’s understandable to feel stirred up when something matters to you. ";
    } else if (/(happy|joy|grateful|calm|peace|content)/.test(emotion)) {
      tonePrefix =
        "I’m glad you’re sharing this—it’s okay to let a gentler moment in. ";
    } else {
      tonePrefix = "Thanks for opening up—I’m here with you. ";
    }
  } else {
    tonePrefix = "Thanks for sharing—I’m here with you. ";
  }

  let body = "";

  if (keyword(/\b(hello|hi|hey)\b/i) && msg.length < 40) {
    body =
      "Hello. I’m SereneMind’s supportive companion. How are you feeling today, in a sentence or two?";
  } else if (keyword(/\b(thanks|thank you|ty)\b/i)) {
    body =
      "You’re welcome. If anything else is on your mind, I’m here to listen.";
  } else if (keyword(/\b(can't sleep|cant sleep|insomnia|tired)\b/i)) {
    body =
      "Rest can get slippery when the mind is busy. If you’d like, try a slow exhale, name one small comfort nearby, and keep tonight’s goal tiny: a little rest, not a perfect night.";
  } else if (keyword(/\b(overwhelm|too much|burnout)\b/i)) {
    body =
      "When everything feels stacked, shrink the next step: one tiny action, one minute of breathing, or one boundary you can hold gently.";
  } else if (keyword(/\b(lonely|alone|isolated)\b/i)) {
    body =
      "Loneliness is a heavy feeling—and reaching out here counts as connection. What would feel supportive in the next hour, even in a small way?";
  } else if (keyword(/\b(scared|afraid|fear)\b/i)) {
    body =
      "Fear can feel loud. Name what you’re afraid might happen, and we can separate facts from worries at your pace.";
  } else if (keyword(/\b(help|support|advice)\b/i)) {
    body =
      "I can’t replace professional care, but I can stay with you. What feels hardest right now—the situation, the feelings in your body, or the thoughts looping?";
  } else {
    body =
      "Would you like to say more about what this is like for you? If it helps, you can share what you need: comfort, perspective, or just someone to stay with you while you unload.";
  }

  const continuityPrefix = hasJournalContinuity
    ? "I am keeping your recent journal reflections in mind. "
    : "";
  const reply = clampReply(`${tonePrefix}${continuityPrefix}${body}`);

  const contextNotes: string[] = [];
  if (emotion != null) {
    contextNotes.push(
      `Personalized using your latest journal mood (“${input.emotionContext.emotion}”).`,
    );
  } else {
    contextNotes.push("No recent journal mood on file.");
  }
  if (hasJournalContinuity) {
    contextNotes.push(
      `Continuity uses ${input.journalContext.selectedEntries.length} recent journal entr${input.journalContext.selectedEntries.length === 1 ? "y" : "ies"}.`,
    );
  }
  const emotionContext = contextNotes.join(" ");

  return { reply, emotionContext };
}
