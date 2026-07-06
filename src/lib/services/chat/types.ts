/**
 * Shared types for chat generation. The mock implementation and a future
 * real LLM adapter should both produce {@link ChatGenerationResult}.
 */
export type EmotionContextForChat = {
  emotion: string | null;
  confidence: number | null;
  emotionMessage: string | null;
  /** ISO date of the journal entry this context came from, if known */
  journalEntryCreatedAt?: string | null;
};

export type ContextJournalEntry = {
  id: string;
  createdAt: string;
  contentExcerpt: string;
  emotion: string | null;
  emotionMessage: string | null;
};

export type AggregatedJournalContext = {
  windowSizeUsed: number;
  selectedEntries: ContextJournalEntry[];
  /**
   * Compact text block that can be forwarded to an LLM provider.
   * Keep this short to avoid unnecessary token usage.
   */
  contextSummary: string;
};

export type ChatGenerationInput = {
  userMessage: string;
  /** Merged client + server journal context used to personalize tone */
  emotionContext: EmotionContextForChat;
  /** Selected recent journal context used for conversational continuity */
  journalContext: AggregatedJournalContext;
};

export type ChatGenerationResult = {
  reply: string;
  /** Short note about which context influenced the reply (mock or model metadata) */
  emotionContext?: string;
};
