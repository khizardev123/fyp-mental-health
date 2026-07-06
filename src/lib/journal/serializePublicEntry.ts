function toIso(value: Date | string): string {
  if (value instanceof Date) return value.toISOString();
  return new Date(value).toISOString();
}

type JournalLike = {
  _id: unknown;
  content: string;
  createdAt: Date;
  updatedAt?: Date;
  emotion?: string | null;
  confidence?: number | null;
  emotionMessage?: string | null;
  contextInsight?: string | null;
  contextInsightUpdatedAt?: Date | null;
};

export type PublicJournalEntry = {
  id: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  emotion: string | null;
  confidence: number | null;
  emotionMessage: string | null;
  contextInsight: string | null;
  contextInsightUpdatedAt: string | null;
};

export function serializePublicJournalEntry(doc: JournalLike): PublicJournalEntry {
  return {
    id: String(doc._id),
    content: doc.content,
    createdAt: toIso(doc.createdAt),
    updatedAt: toIso(doc.updatedAt ?? doc.createdAt),
    emotion: doc.emotion ?? null,
    confidence:
      typeof doc.confidence === "number" && !Number.isNaN(doc.confidence)
        ? doc.confidence
        : null,
    emotionMessage: doc.emotionMessage ?? null,
    contextInsight: doc.contextInsight ?? null,
    contextInsightUpdatedAt: doc.contextInsightUpdatedAt
      ? toIso(doc.contextInsightUpdatedAt)
      : null,
  };
}
