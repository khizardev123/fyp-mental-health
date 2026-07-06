import { describe, expect, it } from "vitest";
import { generateMockChatReply } from "./generateMockChatReply";

describe("generateMockChatReply", () => {
  it("uses calming tone when journal emotion suggests anxiety", () => {
    const out = generateMockChatReply({
      userMessage: "I feel overwhelmed",
      emotionContext: {
        emotion: "anxious",
        confidence: 0.9,
        emotionMessage: "Signs of worry.",
        journalEntryCreatedAt: null,
      },
      journalContext: {
        windowSizeUsed: 1,
        selectedEntries: [
          {
            id: "1",
            createdAt: new Date().toISOString(),
            contentExcerpt: "I have been worried this week.",
            emotion: "anxious",
            emotionMessage: "Stress has been high.",
          },
        ],
        contextSummary: "Entry 1: mood=anxious.",
      },
    });
    expect(out.reply.toLowerCase()).toMatch(/intense|slow|together|overwhelm/);
    expect(out.emotionContext).toMatch(/journal mood/i);
  });

  it("falls back when no emotion context exists", () => {
    const out = generateMockChatReply({
      userMessage: "Hello",
      emotionContext: {
        emotion: null,
        confidence: null,
        emotionMessage: null,
        journalEntryCreatedAt: null,
      },
      journalContext: {
        windowSizeUsed: 0,
        selectedEntries: [],
        contextSummary: "",
      },
    });
    expect(out.reply.length).toBeGreaterThan(10);
    expect(out.emotionContext).toMatch(/no recent journal mood/i);
  });
});
