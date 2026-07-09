'use client';

import { useEffect, useRef, type MutableRefObject } from 'react';
import { drawFaceLandmarks } from '@/lib/faceMeshDraw';
import type { NormalizedLandmark } from '@/lib/faceMeshAnalysis';
import type { FaceTrackingSignals } from '@/lib/faceTrackingTypes';
import { inferFaceEmotionFromSignals } from '@/lib/faceEmotionInference';

const IS_DEV = process.env.NODE_ENV === 'development';
const PREVIEW_W = 240;
const PREVIEW_H = 180;

interface FaceTrackingDebugOverlayProps {
    active: boolean;
    videoRef: MutableRefObject<HTMLVideoElement | null>;
    landmarksRef: MutableRefObject<NormalizedLandmark[] | null>;
    tracking: FaceTrackingSignals;
    textEmotion?: string;
    faceEmotion?: string | null;
    faceConfidence?: number;
}

function MetricRow({ label, value }: { label: string; value: string | number | boolean }) {
    return (
        <div className="flex justify-between gap-3 text-[10px] leading-tight">
            <span className="text-slate-400">{label}</span>
            <span className="font-mono text-emerald-300">{String(value)}</span>
        </div>
    );
}

export default function FaceTrackingDebugOverlay({
    active,
    videoRef,
    landmarksRef,
    tracking,
    textEmotion = 'neutral',
    faceEmotion = null,
    faceConfidence = 0,
}: FaceTrackingDebugOverlayProps) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    useEffect(() => {
        if (!IS_DEV || !active) return;

        let raf = 0;
        const draw = () => {
            const video = videoRef.current;
            const canvas = canvasRef.current;
            if (video && canvas) {
                const w = video.videoWidth || PREVIEW_W;
                const h = video.videoHeight || PREVIEW_H;
                if (canvas.width !== w) canvas.width = w;
                if (canvas.height !== h) canvas.height = h;
                const ctx = canvas.getContext('2d');
                if (ctx) {
                    drawFaceLandmarks(ctx, landmarksRef.current, w, h, false);
                }
            }
            raf = requestAnimationFrame(draw);
        };

        raf = requestAnimationFrame(draw);
        return () => cancelAnimationFrame(raf);
    }, [active, videoRef, landmarksRef]);

    if (!IS_DEV || !active) return null;

    const liveFace = inferFaceEmotionFromSignals(tracking);

    return (
        <div
            className="fixed bottom-4 right-4 z-50 flex gap-2 pointer-events-none"
            aria-hidden
        >
            <div
                className="relative rounded-lg overflow-hidden border border-cyan-500/40 shadow-xl bg-black"
                style={{ width: PREVIEW_W, height: PREVIEW_H }}
            >
                <video
                    ref={videoRef}
                    className="absolute inset-0 w-full h-full object-cover scale-x-[-1]"
                    muted
                    playsInline
                    autoPlay
                />
                <canvas
                    ref={canvasRef}
                    className="absolute inset-0 w-full h-full scale-x-[-1] pointer-events-none"
                />
                <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-black/70 text-[9px] text-cyan-300 font-mono">
                    DEV · MediaPipe
                </div>
            </div>

            <div className="w-44 rounded-lg border border-slate-600/80 bg-slate-900/95 p-2 space-y-1 font-mono shadow-xl">
                <div className="text-[9px] uppercase tracking-wide text-slate-500 mb-1">Face Debug</div>
                <MetricRow label="Text emotion" value={textEmotion} />
                <MetricRow label="Face (live)" value={liveFace.confidence > 0 ? liveFace.emotion : '—'} />
                <MetricRow label="Face (last msg)" value={faceEmotion || '—'} />
                <MetricRow label="Face confidence" value={`${(faceConfidence * 100).toFixed(0)}%`} />
                <MetricRow label="Face detected" value={tracking.faceDetected} />
                <MetricRow label="FPS" value={tracking.fps} />
                <MetricRow label="Blink value" value={tracking.blinkValue.toFixed(2)} />
                <MetricRow label="Left eye" value={tracking.leftEyeOpenness.toFixed(2)} />
                <MetricRow label="Right eye" value={tracking.rightEyeOpenness.toFixed(2)} />
                <MetricRow label="Smile" value={tracking.smileIntensity.toFixed(2)} />
                <MetricRow label="Head yaw" value={tracking.headYaw.toFixed(1)} />
                <MetricRow label="Head pitch" value={tracking.headPitch.toFixed(1)} />
                <MetricRow label="Head roll" value={tracking.headTilt.toFixed(1)} />
                <MetricRow label="Eyebrow raise" value={tracking.eyebrowRaise.toFixed(2)} />
                <MetricRow label="Landmarks" value={tracking.landmarkCount} />
            </div>
        </div>
    );
}
