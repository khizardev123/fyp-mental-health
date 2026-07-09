/**
 * Geometry helpers for MediaPipe Face Mesh landmarks (468 points).
 * Pretrained model output only — no training.
 */

export interface NormalizedLandmark {
    x: number;
    y: number;
    z?: number;
}

const LEFT_EYE = [33, 160, 158, 133, 153, 144];
const RIGHT_EYE = [362, 385, 387, 263, 373, 380];
const LEFT_BROW = [70, 63, 105, 66, 107];
const RIGHT_BROW = [300, 293, 334, 296, 336];
const MOUTH_LEFT = 61;
const MOUTH_RIGHT = 291;
const UPPER_LIP = 13;
const LOWER_LIP = 14;
const NOSE_TIP = 1;
const CHIN = 152;
const LEFT_CHEEK = 234;
const RIGHT_CHEEK = 454;
const FOREHEAD = 10;

function dist(a: NormalizedLandmark, b: NormalizedLandmark): number {
    return Math.hypot(a.x - b.x, a.y - b.y);
}

function eyeAspectRatio(landmarks: NormalizedLandmark[], indices: number[]): number {
    const p = indices.map(i => landmarks[i]);
    const vertical = dist(p[1], p[5]) + dist(p[2], p[4]);
    const horizontal = dist(p[0], p[3]) + 1e-6;
    return vertical / (2 * horizontal);
}

function avgY(landmarks: NormalizedLandmark[], indices: number[]): number {
    return indices.reduce((s, i) => s + landmarks[i].y, 0) / indices.length;
}

export interface FaceMeshMetrics {
    faceDetected: boolean;
    eyeOpenness: number;
    leftEyeOpenness: number;
    rightEyeOpenness: number;
    blinkValue: number;
    blinking: boolean;
    smileIntensity: number;
    eyebrowRaise: number;
    headTilt: number;
    headPitch: number;
    headYaw: number;
    landmarkCount: number;
}

const EAR_BLINK = 0.19;
const EAR_OPEN = 0.28;

function earToOpenness(ear: number): number {
    return Math.max(0, Math.min(1, (ear - EAR_BLINK) / (EAR_OPEN - EAR_BLINK)));
}

export function analyzeFaceMeshLandmarks(landmarks: NormalizedLandmark[] | undefined): FaceMeshMetrics {
    if (!landmarks || landmarks.length < 468) {
        return {
            faceDetected: false,
            eyeOpenness: 1,
            leftEyeOpenness: 1,
            rightEyeOpenness: 1,
            blinkValue: 0,
            blinking: false,
            smileIntensity: 0,
            eyebrowRaise: 0,
            headTilt: 0,
            headPitch: 0,
            headYaw: 0,
            landmarkCount: landmarks?.length ?? 0,
        };
    }

    const leftEar = eyeAspectRatio(landmarks, LEFT_EYE);
    const rightEar = eyeAspectRatio(landmarks, RIGHT_EYE);
    const avgEar = (leftEar + rightEar) / 2;

    const leftEyeOpenness = earToOpenness(leftEar);
    const rightEyeOpenness = earToOpenness(rightEar);
    const eyeOpenness = (leftEyeOpenness + rightEyeOpenness) / 2;
    const blinkValue = Math.max(0, Math.min(1, 1 - eyeOpenness));
    const blinking = avgEar < EAR_BLINK;

    const faceWidth = dist(landmarks[LEFT_CHEEK], landmarks[RIGHT_CHEEK]) + 1e-6;
    const mouthWidth = dist(landmarks[MOUTH_LEFT], landmarks[MOUTH_RIGHT]);
    const mouthHeight = dist(landmarks[UPPER_LIP], landmarks[LOWER_LIP]) + 1e-6;
    const smileRatio = (mouthWidth / faceWidth) * (mouthWidth / mouthHeight);
    const smileIntensity = Math.max(0, Math.min(1, (smileRatio - 0.85) / 0.55));

    const leftBrowY = avgY(landmarks, LEFT_BROW);
    const rightBrowY = avgY(landmarks, RIGHT_BROW);
    const leftEyeY = avgY(landmarks, [159, 145]);
    const rightEyeY = avgY(landmarks, [386, 374]);
    const browGap = ((leftEyeY - leftBrowY) + (rightEyeY - rightBrowY)) / 2;
    const eyebrowRaise = Math.max(0, Math.min(1, (browGap - 0.028) / 0.045));

    const headTilt =
        (Math.atan2(
            landmarks[RIGHT_CHEEK].y - landmarks[LEFT_CHEEK].y,
            landmarks[RIGHT_CHEEK].x - landmarks[LEFT_CHEEK].x,
        ) *
            180) /
        Math.PI;

    const nose = landmarks[NOSE_TIP];
    const chin = landmarks[CHIN];
    const forehead = landmarks[FOREHEAD];
    const faceHeight = dist(forehead, chin) + 1e-6;
    const headPitch = Math.max(-15, Math.min(15, ((nose.y - (forehead.y + chin.y) / 2) / faceHeight) * 60));

    const midX = (landmarks[LEFT_CHEEK].x + landmarks[RIGHT_CHEEK].x) / 2;
    const headYaw = Math.max(-20, Math.min(20, ((nose.x - midX) / (faceWidth * 0.5)) * 25));

    return {
        faceDetected: true,
        eyeOpenness,
        leftEyeOpenness,
        rightEyeOpenness,
        blinkValue,
        blinking,
        smileIntensity,
        eyebrowRaise,
        headTilt,
        headPitch,
        headYaw,
        landmarkCount: landmarks.length,
    };
}
