'use client';

import { useCallback, useRef, useState } from 'react';
import { avatarApi } from '@/lib/api';

interface MouthTiming {
    word: string;
    start_ms: number;
    end_ms: number;
    mouth_open: number;
}

export function useAvatarSpeech() {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [mouthOpen, setMouthOpen] = useState(0);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const rafRef = useRef<number | null>(null);
    const speakGenerationRef = useRef(0);
    const lastSpokenRef = useRef<string>('');

    /** Stop audio/mouth animation without invalidating an in-flight speak generation. */
    const cancelAudioPlayback = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.src = '';
            audioRef.current = null;
        }
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
        setIsSpeaking(false);
        setMouthOpen(0);
    }, []);

    const stopSpeech = useCallback(() => {
        speakGenerationRef.current += 1;
        cancelAudioPlayback();
    }, [cancelAudioPlayback]);

    const animateMouth = useCallback((timings: MouthTiming[], totalMs: number, gen: number) => {
        let current = 0.1;
        const start = performance.now();

        const tick = () => {
            if (speakGenerationRef.current !== gen) return;
            const elapsed = performance.now() - start;
            if (elapsed >= totalMs) {
                setMouthOpen(0);
                setIsSpeaking(false);
                return;
            }
            const active = timings.find(t => elapsed >= t.start_ms && elapsed < t.end_ms);
            const target = active?.mouth_open ?? 0.12;
            current += (target - current) * 0.35;
            setMouthOpen(current);
            rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
    }, []);

    /**
     * Speak once per unique final reply. Call only after SSE `done` and UI flush.
     * Cancels prior audio but keeps this generation valid.
     */
    const speakText = useCallback((text: string, hooks?: {
        onAudioStart?: () => void;
        onComplete?: () => void;
    }) => {
        const clean = text.trim();
        if (!clean) return;
        if (clean === lastSpokenRef.current) return;

        const gen = ++speakGenerationRef.current;
        cancelAudioPlayback();
        lastSpokenRef.current = clean;
        const ttsT0 = performance.now();

        void (async () => {
            if (speakGenerationRef.current !== gen) return;

            try {
                const [speakRes, lipsyncRes] = await Promise.all([
                    avatarApi.speak(clean),
                    avatarApi.lipsync(clean),
                ]);
                const ttsMs = performance.now() - ttsT0;
                if (process.env.NODE_ENV === 'development') {
                    console.debug(`[Pipeline] TTS generation .... ${ttsMs.toFixed(0)} ms`);
                }

                if (speakGenerationRef.current !== gen) return;

                const audioUrl = speakRes.data.url;
                const { timings, total_duration_ms } = lipsyncRes.data;

                const audio = new Audio(audioUrl);
                audioRef.current = audio;

                audio.onended = () => {
                    if (speakGenerationRef.current !== gen) return;
                    setIsSpeaking(false);
                    setMouthOpen(0);
                    audioRef.current = null;
                    hooks?.onComplete?.();
                };
                audio.onerror = () => {
                    if (speakGenerationRef.current === gen) cancelAudioPlayback();
                };

                let mouthStarted = false;
                const onPlay = () => {
                    if (mouthStarted || speakGenerationRef.current !== gen) return;
                    mouthStarted = true;
                    hooks?.onAudioStart?.();
                    setIsSpeaking(true);
                    animateMouth(timings, total_duration_ms, gen);
                };

                audio.addEventListener('playing', onPlay, { once: true });
                await audio.play();
            } catch (err) {
                console.warn('TTS unavailable:', err);
                if (speakGenerationRef.current === gen) {
                    setIsSpeaking(false);
                    setMouthOpen(0);
                }
            }
        })();
    }, [animateMouth, cancelAudioPlayback]);

    const resetSpeakDedup = useCallback(() => {
        lastSpokenRef.current = '';
    }, []);

    return { speakText, stopSpeech, resetSpeakDedup, isSpeaking, mouthOpen };
}
