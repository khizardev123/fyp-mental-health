import { Schema, model, models } from "mongoose";

const JournalSchema = new Schema(
  {
    userId: {
      type: Schema.Types.ObjectId,
      ref: "User",
      required: [true, "User is required"],
      index: true,
    },
    content: {
      type: String,
      required: [true, "Content is required"],
      trim: true,
      maxlength: [50_000, "Journal entry cannot exceed 50,000 characters"],
    },
    emotion: {
      type: String,
      trim: true,
      maxlength: [120, "Emotion label cannot exceed 120 characters"],
      default: null,
    },
    confidence: {
      type: Number,
      min: [0, "Confidence cannot be below 0"],
      max: [1, "Confidence cannot be above 1"],
      default: null,
    },
    emotionMessage: {
      type: String,
      trim: true,
      maxlength: [4000, "Emotion message cannot exceed 4,000 characters"],
      default: null,
    },
    contextInsight: {
      type: String,
      trim: true,
      maxlength: [2_000, "Context insight cannot exceed 2,000 characters"],
      default: null,
    },
    contextInsightUpdatedAt: {
      type: Date,
      default: null,
    },
  },
  { timestamps: true },
);

export const Journal = models.Journal ?? model("Journal", JournalSchema);
