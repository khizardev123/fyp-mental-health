'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { analyzeFaceMeshLandmarks, NormalizedLandmark } from '@/lib/faceMeshAnalysis';
import { DEFAULT_FACE_TRACKING, FaceTrackingSignals } from '@/lib/faceTrackingTypes';

const DEBUG = process.env.NODE_ENV === 'development';
const LOG_INTERVAL_MS = 1500;

function logDebug(message: string, data?: Record<string, unknown>) {
    if (!DEBUG) return;
    if (data) {
        console.debug(`[MediaPipe] ${message}`, data);
    } else {
        console.debug(`[MediaPipe] ${message}`);
    }
}

export function useMediaPipeFaceMesh(enabled: boolean) {
    const [trackingEnabled, setTrackingEnabled] = useState(enabled);
    const [faceTracking, setFaceTracking] = useState<FaceTrackingSignals>(DEFAULT_FACE_TRACKING);
    const [initialized, setInitialized] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const videoRef = useRef<HTMLVideoElement | null>(null);
    const landmarksRef = useRef<NormalizedLandmark[] | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const faceMeshRef = useRef<any>(null);
    const cameraRef = useRef<any>(null);
    const lastLogRef = useRef(0);
    const prevBlinkRef = useRef(false);
    const frameCountRef = useRef(0);
    const lastFpsTimeRef = useRef(performance.now());
    const fpsRef = useRef(0);

    const onResults = useCallback((results: any) => {
        frameCountRef.current += 1;
        const now = performance.now();
        if (now - lastFpsTimeRef.current >= 1000) {
            fpsRef.current = frameCountRef.current;
            frameCountRef.current = 0;
            lastFpsTimeRef.current = now;
        }

        const landmarks = results.multiFaceLandmarks?.[0] as NormalizedLandmark[] | undefined;
        landmarksRef.current = landmarks ?? null;
        const metrics = analyzeFaceMeshLandmarks(landmarks);

        if (metrics.blinking && !prevBlinkRef.current) {
            logDebug('Blink detected');
        }
        prevBlinkRef.current = metrics.blinking;

        if (metrics.smileIntensity > 0.45 && now - lastLogRef.current > LOG_INTERVAL_MS) {
            logDebug('Smile detected', { intensity: metrics.smileIntensity.toFixed(2) });
        }

        const signals: FaceTrackingSignals = {
            faceDetected: metrics.faceDetected,
            blinking: metrics.blinking,
            blinkValue: metrics.blinkValue,
            headTilt: metrics.headTilt,
            headPitch: metrics.headPitch,
            headYaw: metrics.headYaw,
            eyeOpenness: metrics.eyeOpenness,
            leftEyeOpenness: metrics.leftEyeOpenness,
            rightEyeOpenness: metrics.rightEyeOpenness,
            smileIntensity: metrics.smileIntensity,
            eyebrowRaise: metrics.eyebrowRaise,
            landmarkCount: metrics.landmarkCount,
            fps: fpsRef.current,
        };

        setFaceTracking(signals);

        if (now - lastLogRef.current > LOG_INTERVAL_MS) {
            lastLogRef.current = now;
            if (metrics.faceDetected) {
                logDebug('Face detected');
                logDebug('Head rotation', {
                    tilt: metrics.headTilt.toFixed(1),
                    pitch: metrics.headPitch.toFixed(1),
                    yaw: metrics.headYaw.toFixed(1),
                });
                logDebug('Eye openness', { value: metrics.eyeOpenness.toFixed(2) });
                logDebug('FPS', { value: fpsRef.current });
            }
        }
    }, []);

    useEffect(() => {
        if (!trackingEnabled) {
            setFaceTracking(DEFAULT_FACE_TRACKING);
            landmarksRef.current = null;
            return;
        }

        let cancelled = false;

        async function start() {
            try {
                const [{ FaceMesh }, { Camera }] = await Promise.all([
                    import('@mediapipe/face_mesh'),
                    import('@mediapipe/camera_utils'),
                ]);

                if (cancelled) return;

                const faceMesh = new FaceMesh({
                    locateFile: (file: string) =>
                        `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
                });

                faceMesh.setOptions({
                    maxNumFaces: 1,
                    refineLandmarks: true,
                    minDetectionConfidence: 0.5,
                    minTrackingConfidence: 0.5,
                });

                faceMesh.onResults(onResults);
                faceMeshRef.current = faceMesh;

                logDebug('MediaPipe initialized');

                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: 640, height: 480 },
                    audio: false,
                });

                if (cancelled) {
                    stream.getTracks().forEach(t => t.stop());
                    return;
                }

                streamRef.current = stream;

                const waitForVideo = () =>
                    new Promise<HTMLVideoElement>((resolve, reject) => {
                        const deadline = Date.now() + 3000;
                        const tick = () => {
                            const video = videoRef.current;
                            if (video) return resolve(video);
                            if (Date.now() > deadline) return reject(new Error('Video element not ready'));
                            requestAnimationFrame(tick);
                        };
                        tick();
                    });

                const video = await waitForVideo();
                if (cancelled) {
                    stream.getTracks().forEach(t => t.stop());
                    return;
                }

                video.srcObject = stream;
                await video.play();

                const camera = new Camera(video, {
                    onFrame: async () => {
                        if (faceMeshRef.current && videoRef.current) {
                            await faceMeshRef.current.send({ image: videoRef.current });
                        }
                    },
                    width: 640,
                    height: 480,
                });

                cameraRef.current = camera;
                await camera.start();
                setInitialized(true);
                setError(null);
            } catch (err: any) {
                console.warn('[MediaPipe] Failed to start:', err);
                setError(err?.message || 'Camera or MediaPipe unavailable');
                setTrackingEnabled(false);
            }
        }

        start();

        return () => {
            cancelled = true;
            cameraRef.current?.stop?.();
            cameraRef.current = null;
            faceMeshRef.current?.close?.();
            faceMeshRef.current = null;
            streamRef.current?.getTracks().forEach(t => t.stop());
            streamRef.current = null;
            landmarksRef.current = null;
            setInitialized(false);
        };
    }, [trackingEnabled, onResults]);

    return {
        faceTracking,
        trackingEnabled,
        setTrackingEnabled,
        initialized,
        error,
        videoRef,
        landmarksRef,
    };
}
