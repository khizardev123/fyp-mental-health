/** Browser-side MediaPipe face animation signals (no backend). */
export interface FaceTrackingSignals {
    faceDetected: boolean;
    blinking: boolean;
    blinkValue: number;
    headTilt: number;
    headPitch: number;
    headYaw: number;
    eyeOpenness: number;
    leftEyeOpenness: number;
    rightEyeOpenness: number;
    smileIntensity: number;
    eyebrowRaise: number;
    landmarkCount: number;
    fps: number;
}

export const DEFAULT_FACE_TRACKING: FaceTrackingSignals = {
    faceDetected: false,
    blinking: false,
    blinkValue: 0,
    headTilt: 0,
    headPitch: 0,
    headYaw: 0,
    eyeOpenness: 1,
    leftEyeOpenness: 1,
    rightEyeOpenness: 1,
    smileIntensity: 0,
    eyebrowRaise: 0,
    landmarkCount: 0,
    fps: 0,
};
