import { z } from "zod";

export const emotionContextSchema = z.object({
  emotion: z.string().trim().max(120).nullable().optional(),
  confidence: z.number().min(0).max(1).nullable().optional(),
  emotionMessage: z.string().trim().max(4000).nullable().optional(),
  journalEntryCreatedAt: z.string().trim().max(80).nullable().optional(),
});

export const chatRequestSchema = z.object({
  message: z
    .string()
    .trim()
    .min(1, "Message cannot be empty.")
    .max(8_000, "Message is too long."),
  emotionContext: emotionContextSchema.optional(),
  contextWindowSize: z.number().int().min(1).max(10).optional(),
});

export type ChatRequestBody = z.infer<typeof chatRequestSchema>;
