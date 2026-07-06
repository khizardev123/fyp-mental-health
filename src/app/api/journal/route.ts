import { NextRequest, NextResponse } from "next/server";
import { connectDB } from "@/lib/db";
import { Journal } from "@/models/Journal";
import { getAuthenticatedUser } from "@/lib/auth/session";
import { journalCreateSchema } from "@/lib/validation/journal";
import { mapInfrastructureFailure } from "@/lib/server/mapInfrastructureFailure";
import { analyzeEmotion } from "@/lib/services/emotion/analyzeEmotion";
import { serializePublicJournalEntry } from "@/lib/journal/serializePublicEntry";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const session = await getAuthenticatedUser();
    if (!session?.sub) {
      return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
    }

    await connectDB();

    const rawLimit = request.nextUrl.searchParams.get("limit");
    const parsedLimit = rawLimit ? Number.parseInt(rawLimit, 10) : null;
    const limit =
      parsedLimit && Number.isFinite(parsedLimit)
        ? Math.min(100, Math.max(1, parsedLimit))
        : null;

    const query = Journal.find({ userId: session.sub }).sort({ createdAt: -1 });
    if (limit) {
      query.limit(limit);
    }
    const docs = await query.lean();

    const entries = docs.map((doc) =>
      serializePublicJournalEntry({
        _id: doc._id,
        content: doc.content,
        createdAt: doc.createdAt,
        updatedAt: doc.updatedAt,
        emotion: doc.emotion ?? null,
        confidence: doc.confidence ?? null,
        emotionMessage: doc.emotionMessage ?? null,
        contextInsight: doc.contextInsight ?? null,
        contextInsightUpdatedAt: doc.contextInsightUpdatedAt ?? null,
      }),
    );

    return NextResponse.json({ entries });
  } catch (err: unknown) {
    const infra = mapInfrastructureFailure(err);
    if (infra) return NextResponse.json(infra.body, { status: infra.status });
    console.error("[api/journal GET]", err);
    return NextResponse.json(
      { error: "Something went wrong." },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getAuthenticatedUser();
    if (!session?.sub) {
      return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
    }

    let json: unknown;
    try {
      json = await request.json();
    } catch {
      return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
    }

    const parsed = journalCreateSchema.safeParse(json);
    if (!parsed.success) {
      return NextResponse.json(
        {
          error: "Validation failed.",
          fieldErrors: parsed.error.flatten().fieldErrors,
        },
        { status: 400 },
      );
    }

    await connectDB();

    const entry = await Journal.create({
      userId: session.sub,
      content: parsed.data.content,
    });

    let doc = await Journal.findById(entry._id).lean();
    if (!doc) {
      return NextResponse.json({ error: "Something went wrong." }, { status: 500 });
    }

    try {
      const analysis = await analyzeEmotion(parsed.data.content);
      const updated = await Journal.findByIdAndUpdate(
        entry._id,
        {
          $set: {
            emotion: analysis.emotion,
            confidence: analysis.confidence,
            emotionMessage: analysis.message,
          },
        },
        { new: true, runValidators: true },
      ).lean();
      if (updated) doc = updated;
    } catch (emotionErr: unknown) {
      console.warn("[api/journal POST] Emotion analysis skipped:", emotionErr);
    }

    return NextResponse.json(
      {
        success: true,
        message: "Journal entry saved.",
        entry: serializePublicJournalEntry(doc),
      },
      { status: 201 },
    );
  } catch (err: unknown) {
    const infra = mapInfrastructureFailure(err);
    if (infra) return NextResponse.json(infra.body, { status: infra.status });
    console.error("[api/journal POST]", err);
    return NextResponse.json(
      { error: "Something went wrong." },
      { status: 500 },
    );
  }
}
