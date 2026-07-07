'use client';

import { useCallback, useRef } from 'react';

/**
 * Buffers streaming chunks and flushes on animation frames.
 * Backend already emits phrase-sized chunks — avoid extra debounce jitter.
 */
export function useStreamBuffer() {
    const textRef = useRef('');
    const pendingRef = useRef('');
    const rafRef = useRef<number | null>(null);
    const onUpdateRef = useRef<((text: string) => void) | null>(null);

    const reset = useCallback(() => {
        textRef.current = '';
        pendingRef.current = '';
        onUpdateRef.current = null;
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
    }, []);

    const scheduleFlush = useCallback(() => {
        if (rafRef.current !== null) return;
        rafRef.current = requestAnimationFrame(() => {
            rafRef.current = null;
            if (pendingRef.current) {
                textRef.current += pendingRef.current;
                pendingRef.current = '';
            }
            onUpdateRef.current?.(textRef.current);
        });
    }, []);

    const flushNow = useCallback((onUpdate: (text: string) => void) => {
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
        if (pendingRef.current) {
            textRef.current += pendingRef.current;
            pendingRef.current = '';
        }
        onUpdate(textRef.current);
    }, []);

    const appendChunk = useCallback((
        chunk: string,
        onUpdate: (text: string) => void,
    ) => {
        onUpdateRef.current = onUpdate;
        pendingRef.current += chunk;
        scheduleFlush();
    }, [scheduleFlush]);

    const setFinal = useCallback((text: string) => {
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
        pendingRef.current = '';
        textRef.current = text;
    }, []);

    return { reset, appendChunk, flushNow, setFinal, getText: () => textRef.current };
}
