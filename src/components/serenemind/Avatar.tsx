"use client";

import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createAvatar } from '@dicebear/core';
import { avataaars } from '@dicebear/collection';
import { normalizeAvatarEmotion, AvatarEmotionState } from '@/lib/serenemind/emotionFusion';
import type { FaceTrackingSignals } from '@/lib/serenemind/faceTrackingTypes';

interface AvatarProps {
    emotion: string;
    isThinking: boolean;
    mouthOpen?: number;
    isSpeaking?: boolean;
    /** Browser MediaPipe face signals — animation only, not emotion source */
    faceTracking?: FaceTrackingSignals | null;
}

type EmotionConfig = {
    mouth: string[];
    eyes: string[];
    eyebrows: string[];
    headTilt: number;
    headNod: number;
    blinkMin: number;
    blinkMax: number;
    breathDuration: number;
    eyebrowLift: number;
    scale: number;
};

const EMOTION_CONFIG: Record<AvatarEmotionState, EmotionConfig> = {
    happy: {
        mouth: ['smile', 'laughing'],
        eyes: ['happy', 'wink'],
        eyebrows: ['default', 'raisedExcited'],
        headTilt: 2,
        headNod: 0,
        blinkMin: 2.8,
        blinkMax: 5.2,
        breathDuration: 3.2,
        eyebrowLift: -2,
        scale: 1.02,
    },
    sad: {
        mouth: ['sad', 'pucker'],
        eyes: ['squint', 'closed'],
        eyebrows: ['sadConcerned', 'default'],
        headTilt: 7,
        headNod: 3,
        blinkMin: 3.5,
        blinkMax: 6.5,
        breathDuration: 4.8,
        eyebrowLift: 3,
        scale: 0.98,
    },
    angry: {
        mouth: ['grimace', 'serious'],
        eyes: ['angry', 'side'],
        eyebrows: ['angry', 'angryNatural'],
        headTilt: -4,
        headNod: 0,
        blinkMin: 3,
        blinkMax: 5.5,
        breathDuration: 2.8,
        eyebrowLift: 4,
        scale: 1,
    },
    anxious: {
        mouth: ['concerned', 'serious'],
        eyes: ['surprised', 'eyeRoll'],
        eyebrows: ['raisedExcitedNatural', 'default'],
        headTilt: 0,
        headNod: 0,
        blinkMin: 1.6,
        blinkMax: 3.2,
        breathDuration: 2.2,
        eyebrowLift: -4,
        scale: 1,
    },
    neutral: {
        mouth: ['default', 'smile'],
        eyes: ['default'],
        eyebrows: ['default', 'flatNatural'],
        headTilt: 0,
        headNod: 0,
        blinkMin: 3,
        blinkMax: 6,
        breathDuration: 3.8,
        eyebrowLift: 0,
        scale: 1,
    },
};

const MOUTH_STAGES = {
    closed: ['default', 'serious'],
    mid: ['smile', 'concerned'],
    open: ['surprised', 'eating'],
    wide: ['screamOpen', 'surprised'],
} as const;

type MouthStage = keyof typeof MOUTH_STAGES;

function mouthStageFromOpen(open: number, speaking: boolean): MouthStage {
    if (!speaking || open < 0.12) return 'closed';
    if (open < 0.38) return 'mid';
    if (open < 0.68) return 'open';
    return 'wide';
}

function buildAvatarUri(
    config: EmotionConfig,
    eyebrowIndex: number,
    mouthStage: MouthStage,
) {
    const brows = config.eyebrows;
    const brow = brows[eyebrowIndex % brows.length] ?? brows[0];
    const mouth = MOUTH_STAGES[mouthStage];

    const avatar = createAvatar(avataaars, {
        seed: 'SereneMind',
        backgroundColor: ['b6e3f4', 'c0aede', 'd1d4f9'],
        backgroundType: ['gradientLinear'],
        mouth: mouth as any,
        eyes: config.eyes as any,
        eyebrows: [brow] as any,
        clothing: ['graphicShirt', 'hoodie', 'overall'],
        top: ['shortHair', 'longHiTop', 'shaggyMullet', 'shortCurly'] as any,
        hairColor: ['2e1505', '4e1b0b', 'b58143'],
        accessories: ['round', 'prescription01'],
        clothesColor: ['262e33', '65c9ff', '5199e4'],
    });
    return avatar.toDataUri();
}

function useBlinkTiming(minSec: number, maxSec: number) {
    const [blinking, setBlinking] = useState(false);

    useEffect(() => {
        let cancelled = false;
        let timeoutId: ReturnType<typeof setTimeout>;

        const schedule = () => {
            const pause = (minSec + Math.random() * (maxSec - minSec)) * 1000;
            timeoutId = setTimeout(() => {
                if (cancelled) return;
                setBlinking(true);
                timeoutId = setTimeout(() => {
                    if (cancelled) return;
                    setBlinking(false);
                    schedule();
                }, 110 + Math.random() * 40);
            }, pause);
        };

        schedule();
        return () => {
            cancelled = true;
            clearTimeout(timeoutId);
        };
    }, [minSec, maxSec]);

    return blinking;
}

function useEyebrowCycle(length: number, intervalMs = 3200) {
    const [index, setIndex] = useState(0);

    useEffect(() => {
        if (length <= 1) return;
        const id = setInterval(() => {
            setIndex(prev => (prev + 1) % length);
        }, intervalMs);
        return () => clearInterval(id);
    }, [length, intervalMs]);

    return index;
}

const springTransition = { type: 'spring' as const, stiffness: 80, damping: 18 };

export default function Avatar({
    emotion,
    isThinking,
    mouthOpen = 0,
    isSpeaking = false,
    faceTracking = null,
}: AvatarProps) {
    const targetState = normalizeAvatarEmotion(emotion);
    const [displayState, setDisplayState] = useState<AvatarEmotionState>(targetState);
    const prevStateRef = useRef(targetState);

    useEffect(() => {
        if (targetState === prevStateRef.current) return;
        const t = setTimeout(() => {
            setDisplayState(targetState);
            prevStateRef.current = targetState;
        }, 80);
        return () => clearTimeout(t);
    }, [targetState]);

    const config = EMOTION_CONFIG[displayState];
    const blinkingAuto = useBlinkTiming(config.blinkMin, config.blinkMax);
    const trackingActive = Boolean(faceTracking?.faceDetected);
    const blinking = trackingActive
        ? faceTracking!.blinking || faceTracking!.eyeOpenness < 0.35
        : blinkingAuto;
    const browIndex = useEyebrowCycle(config.eyebrows.length);
    let mouthStage = mouthStageFromOpen(mouthOpen, isSpeaking);
    if (trackingActive && faceTracking!.smileIntensity > 0.35) {
        mouthStage = faceTracking!.smileIntensity > 0.65 ? 'open' : 'mid';
    }

    const headTilt = config.headTilt + (trackingActive ? faceTracking!.headTilt * 0.45 : 0);
    const headYawOffset = trackingActive ? faceTracking!.headYaw * 0.35 : 0;
    const headPitchOffset = trackingActive ? faceTracking!.headPitch * 0.25 : 0;
    const eyebrowLift =
        config.eyebrowLift
        - (trackingActive ? faceTracking!.eyebrowRaise * 10 : 0)
        + (blinking ? 2 : 0);
    const eyeClosedAmount = trackingActive
        ? Math.max(blinking ? 1 : 0, 1 - faceTracking!.eyeOpenness)
        : (blinking ? 1 : 0);

    const avatarUri = useMemo(
        () => buildAvatarUri(config, browIndex, mouthStage),
        [config, browIndex, mouthStage],
    );

    const anxiousWobble = displayState === 'anxious' && !isThinking;
    const mouthScaleY = isSpeaking ? 0.45 + mouthOpen * 0.65 : 1;

    return (
        <div className="relative w-32 h-32 flex items-center justify-center">
            <motion.div
                className="absolute inset-0 blur-3xl rounded-full bg-indigo-500/20"
                animate={{
                    scale: isThinking ? [1, 1.25, 1] : [1, 1.06, 1],
                    opacity: [0.28, 0.5, 0.28],
                }}
                transition={{
                    duration: isThinking ? 1.8 : config.breathDuration,
                    repeat: Infinity,
                    ease: 'easeInOut',
                }}
            />

            <motion.div
                className="relative w-full h-full rounded-full overflow-hidden border-2 border-white/10 shadow-2xl bg-slate-900"
                animate={{
                    rotateZ: headTilt,
                    rotateY: headYawOffset,
                    rotateX: headPitchOffset,
                    scale: isThinking ? 0.96 : config.scale,
                    y: isThinking
                        ? [0, -2, 0]
                        : displayState === 'sad'
                            ? [0, 2.5, 0]
                            : [0, -1.2, 0],
                    rotate: anxiousWobble ? [0, -1.2, 1.2, -0.8, 0.8, 0] : isThinking ? [0, -1.5, 1.5, 0] : 0,
                }}
                transition={{
                    rotateZ: springTransition,
                    scale: springTransition,
                    y: {
                        duration: config.breathDuration,
                        repeat: Infinity,
                        ease: 'easeInOut',
                    },
                    rotate: {
                        duration: anxiousWobble ? 2.8 : 2.4,
                        repeat: Infinity,
                        ease: 'easeInOut',
                    },
                }}
            >
                <motion.div
                    className="relative w-full h-full origin-center"
                    animate={{ y: config.headNod }}
                    transition={springTransition}
                >
                    <AnimatePresence mode="sync">
                        <motion.img
                            key={`${displayState}-${mouthStage}-${browIndex}`}
                            src={avatarUri}
                            alt="SereneMind AI Avatar"
                            className="w-full h-full object-cover"
                            initial={{ opacity: 0.4, scale: 0.97 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0.35, scale: 0.98 }}
                            transition={{ duration: 0.55, ease: 'easeInOut' }}
                        />
                    </AnimatePresence>

                    <motion.div
                        className="absolute inset-x-5 top-[18%] flex justify-between pointer-events-none"
                        animate={{ y: eyebrowLift }}
                        transition={{ type: 'spring', stiffness: 180, damping: 18 }}
                    >
                        <div className="w-5 h-1 rounded-full bg-slate-900/25 blur-[0.5px]" />
                        <div className="w-5 h-1 rounded-full bg-slate-900/25 blur-[0.5px]" />
                    </motion.div>

                    <motion.div
                        className="absolute left-1/2 -translate-x-1/2 bottom-[28%] w-8 h-3 rounded-full bg-slate-900/30 pointer-events-none origin-center"
                        animate={{
                            scaleY: mouthScaleY,
                            opacity: isSpeaking ? 0.3 + mouthOpen * 0.45 : 0,
                        }}
                        transition={{ type: 'spring', stiffness: 280, damping: 20 }}
                    />

                    <motion.div
                        className="absolute inset-x-3 top-[20%] h-[22%] bg-slate-900 pointer-events-none origin-center"
                        animate={{
                            scaleY: eyeClosedAmount,
                            opacity: eyeClosedAmount > 0.05 ? 0.92 : 0,
                        }}
                        transition={{
                            scaleY: { duration: eyeClosedAmount > 0.5 ? 0.09 : 0.14, ease: 'easeIn' },
                            opacity: { duration: 0.08 },
                        }}
                    />
                </motion.div>

                <div className="absolute inset-0 pointer-events-none bg-gradient-to-tr from-white/5 to-transparent mix-blend-overlay" />
            </motion.div>

            {isThinking && (
                <div className="absolute -bottom-2 flex gap-1 bg-slate-800 px-2 py-1 rounded-full border border-slate-700 shadow-lg">
                    {[0, 1, 2].map(i => (
                        <motion.div
                            key={i}
                            className="w-1.5 h-1.5 bg-indigo-400 rounded-full"
                            animate={{ opacity: [0.3, 1, 0.3] }}
                            transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                        />
                    ))}
                </div>
            )}

            {isSpeaking && (
                <motion.div
                    className="absolute -bottom-1 w-8 h-1 bg-emerald-400/60 rounded-full origin-center"
                    animate={{ scaleX: [0.5 + mouthOpen * 0.3, 1, 0.5 + mouthOpen * 0.3] }}
                    transition={{ duration: 0.22, repeat: Infinity, ease: 'easeInOut' }}
                />
            )}
        </div>
    );
}
