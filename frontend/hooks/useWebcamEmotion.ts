'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { avatarApi } from '@/lib/api';

export function useWebcamEmotion(enabled: boolean, intervalMs = 5000) {
    const [faceEmotion, setFaceEmotion] = useState<string | null>(null);
    const [faceConfidence, setFaceConfidence] = useState(0);
    const [webcamEnabled, setWebcamEnabled] = useState(enabled);
    const [deepfaceAvailable, setDeepfaceAvailable] = useState<boolean | null>(null);
    const [deepfaceMessage, setDeepfaceMessage] = useState<string | null>(null);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    useEffect(() => {
        avatarApi.getFaceStatus()
            .then(res => {
                setDeepfaceAvailable(res.data.available === true);
                setDeepfaceMessage(res.data.message || null);
            })
            .catch(() => {
                setDeepfaceAvailable(false);
                setDeepfaceMessage('Face emotion service unreachable');
            });
    }, []);

    const captureAndAnalyze = useCallback(async () => {
        if (!webcamEnabled || !videoRef.current || !canvasRef.current) return;
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (video.readyState < 2) return;

        canvas.width = video.videoWidth || 320;
        canvas.height = video.videoHeight || 240;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.7);

        try {
            const res = await avatarApi.analyzeFace(dataUrl);
            if (res.data.available === false) {
                setDeepfaceAvailable(false);
                setDeepfaceMessage(res.data.error || res.data.message || 'DeepFace unavailable');
                return;
            }
            setDeepfaceAvailable(true);
            setFaceEmotion(res.data.emotion);
            setFaceConfidence(res.data.confidence || 0);
        } catch {
            setDeepfaceAvailable(false);
        }
    }, [webcamEnabled]);

    useEffect(() => {
        if (!webcamEnabled) return;

        let interval: ReturnType<typeof setInterval>;
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 320, height: 240 } })
            .then(stream => {
                streamRef.current = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.play().catch(() => {});
                }
                interval = setInterval(captureAndAnalyze, intervalMs);
            })
            .catch(() => setWebcamEnabled(false));

        return () => {
            clearInterval(interval);
            streamRef.current?.getTracks().forEach(t => t.stop());
        };
    }, [webcamEnabled, intervalMs, captureAndAnalyze]);

    return {
        faceEmotion,
        faceConfidence,
        webcamEnabled,
        setWebcamEnabled,
        deepfaceAvailable,
        deepfaceMessage,
        videoRef,
        canvasRef,
    };
}
