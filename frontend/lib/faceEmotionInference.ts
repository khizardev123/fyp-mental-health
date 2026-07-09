import type { FaceTrackingSignals } from '@/lib/faceTrackingTypes';

export interface InferredFaceEmotion {
    emotion: string;
    confidence: number;
}

/** Heuristic face emotion from MediaPipe geometry (browser-only, no ML training). */
export function inferFaceEmotionFromSignals(signals: FaceTrackingSignals | null): InferredFaceEmotion {
    if (!signals?.faceDetected) {
        return { emotion: 'neutral', confidence: 0 };
    }

    const scores: Record<string, number> = {
        happy: 0.05,
        sad: 0.05,
        anxious: 0.05,
        neutral: 0.2,
    };

    if (signals.smileIntensity > 0.4) {
        scores.happy += signals.smileIntensity * 0.85;
    }
    if (signals.smileIntensity < 0.2 && signals.eyeOpenness < 0.45) {
        scores.sad += (1 - signals.eyeOpenness) * 0.5;
    }
    if (signals.eyebrowRaise > 0.35 && signals.smileIntensity < 0.3) {
        scores.anxious += signals.eyebrowRaise * 0.55;
    }
    if (signals.headPitch > 2.5 && signals.smileIntensity < 0.25) {
        scores.sad += 0.25;
    }
    if (signals.blinkValue > 0.6 && signals.smileIntensity < 0.2) {
        scores.sad += 0.15;
    }

    const ranked = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    const [emotion, score] = ranked[0];
    const confidence = Math.max(0, Math.min(1, score));

    return {
        emotion: confidence < 0.28 ? 'neutral' : emotion,
        confidence: confidence < 0.28 ? 0 : confidence,
    };
}
