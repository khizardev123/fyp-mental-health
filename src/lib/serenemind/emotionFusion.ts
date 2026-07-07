export type AvatarEmotionState = 'happy' | 'sad' | 'angry' | 'anxious' | 'neutral';

const ALIASES: Record<string, AvatarEmotionState> = {
    joy: 'happy', happy: 'happy', love: 'happy',
    sadness: 'sad', sad: 'sad', grief: 'sad', depression: 'sad',
    anger: 'angry', angry: 'angry', disgust: 'angry',
    fear: 'anxious', anxiety: 'anxious', anxious: 'anxious', stress: 'anxious',
    neutral: 'neutral', normal: 'neutral',
};

export function normalizeAvatarEmotion(emotion: string | null | undefined): AvatarEmotionState {
    if (!emotion) return 'neutral';
    return ALIASES[emotion.toLowerCase()] || 'neutral';
}

export function fuseEmotions(
    textEmotion: string,
    faceEmotion: string | null,
    faceConfidence: number,
): { text_emotion: AvatarEmotionState; face_emotion: AvatarEmotionState | null; final_avatar_emotion: AvatarEmotionState } {
    const text = normalizeAvatarEmotion(textEmotion);
    const face = faceEmotion ? normalizeAvatarEmotion(faceEmotion) : null;

    if (!face || faceConfidence < 0.25) {
        return { text_emotion: text, face_emotion: face, final_avatar_emotion: text };
    }

    const scores: Record<AvatarEmotionState, number> = {
        happy: 0, sad: 0, angry: 0, anxious: 0, neutral: 0,
    };
    scores[text] += 0.8;
    scores[face] += 0.2 * faceConfidence;

    const final = (Object.entries(scores).sort((a, b) => b[1] - a[1])[0][0]) as AvatarEmotionState;
    return { text_emotion: text, face_emotion: face, final_avatar_emotion: final };
}

export function isStressEmotion(emotion: string): boolean {
    const e = emotion.toLowerCase();
    return ['stress', 'anxious', 'anxiety', 'fear', 'fearful'].includes(e);
}
