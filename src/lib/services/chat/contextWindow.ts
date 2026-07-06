import { Journal } from "@/models/Journal";
import type { AggregatedJournalContext, ContextJournalEntry } from "./types";

const MIN_CONTEXT_WINDOW = 3;
const MAX_CONTEXT_WINDOW = 5;
const DEFAULT_CONTEXT_WINDOW = 5;

const MAX_SELECTED_ENTRIES = 3;
const CONTENT_EXCERPT_MAX_CHARS = 260;
const EMOTION_MESSAGE_MAX_CHARS = 180;
const CONTEXT_SUMMARY_MAX_CHARS = 1_200;

type JournalContextDoc = {
  _id: unknown;
  content: string;
  createdAt: Date | string;
  emotion?: string | null;
  emotionMessage?: string | null;
};

function clampWindowSize(value: number | undefined): number {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return DEFAULT_CONTEXT_WINDOW;
  }
  return Math.min(MAX_CONTEXT_WINDOW, Math.max(MIN_CONTEXT_WINDOW, Math.round(value)));
}

function clampText(text: string, maxChars: number): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= maxChars) return clean;
  return `${clean.slice(0, maxChars - 1).trimEnd()}…`;
}

function tokenize(value: string): Set<string> {
  const tokens = value
    .toLowerCase()
    .split(/[^a-z0-9]+/i)
    .map((t) => t.trim())
    .filter((t) => t.length >= 3);
  return new Set(tokens);
}

function scoreEntryRelevance(
  entry: ContextJournalEntry,
  userTokens: Set<string>,
): number {
  if (userTokens.size === 0) return 0;
  const entryTokens = tokenize(
    `${entry.contentExcerpt} ${entry.emotion ?? ""} ${entry.emotionMessage ?? ""}`,
  );
  let score = 0;
  for (const token of userTokens) {
    if (entryTokens.has(token)) score += 1;
  }
  return score;
}

function normalizeContextDoc(doc: JournalContextDoc): ContextJournalEntry {
  const createdAtIso =
    doc.createdAt instanceof Date
      ? doc.createdAt.toISOString()
      : new Date(doc.createdAt).toISOString();

  return {
    id: String(doc._id),
    createdAt: createdAtIso,
    contentExcerpt: clampText(doc.content, CONTENT_EXCERPT_MAX_CHARS),
    emotion: doc.emotion ?? null,
    emotionMessage: doc.emotionMessage
      ? clampText(doc.emotionMessage, EMOTION_MESSAGE_MAX_CHARS)
      : null,
  };
}

export async function fetchRecentJournalEntriesForContext(params: {
  userId: string;
  requestedWindowSize?: number;
}): Promise<ContextJournalEntry[]> {
  const windowSize = clampWindowSize(params.requestedWindowSize);

  const docs = await Journal.find({
    userId: params.userId,
    content: { $type: "string", $ne: "" },
  })
    .sort({ createdAt: -1 })
    .limit(windowSize)
    .select({ content: 1, createdAt: 1, emotion: 1, emotionMessage: 1 })
    .lean<JournalContextDoc[]>();

  return docs.map(normalizeContextDoc);
}

export function aggregateJournalContext(params: {
  currentMessage: string;
  recentEntries: ContextJournalEntry[];
}): AggregatedJournalContext {
  const userTokens = tokenize(params.currentMessage);
  const scored = params.recentEntries.map((entry) => ({
    entry,
    score: scoreEntryRelevance(entry, userTokens),
  }));

  const hasRelevantMatches = scored.some((item) => item.score > 0);
  const selected = (hasRelevantMatches
    ? scored.sort((a, b) => b.score - a.score).map((item) => item.entry)
    : params.recentEntries
  ).slice(0, MAX_SELECTED_ENTRIES);

  const summaryLines = selected.map((entry, idx) => {
    const moodPart = entry.emotion ? `mood=${entry.emotion}; ` : "";
    const emotionNote = entry.emotionMessage
      ? `emotionNote=${entry.emotionMessage}; `
      : "";
    return `Entry ${idx + 1} (${entry.createdAt}): ${moodPart}${emotionNote}journal=${entry.contentExcerpt}`;
  });

  const contextSummary = clampText(
    summaryLines.join("\n"),
    CONTEXT_SUMMARY_MAX_CHARS,
  );

  return {
    windowSizeUsed: params.recentEntries.length,
    selectedEntries: selected,
    contextSummary,
  };
}
