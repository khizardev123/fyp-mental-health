/** Client-side pipeline timing (development diagnostics). */

export interface ClientPipelineTiming {
    messageSentMs: number;
    metaReceivedMs: number;
    firstChunkMs: number;
    doneReceivedMs: number;
    ttsStartMs: number;
    audioPlaybackMs: number;
    avatarUpdateMs: number;
}

const IS_DEV = process.env.NODE_ENV === 'development';

type PipelineMark =
    | 'sent'
    | 'meta'
    | 'firstChunk'
    | 'done'
    | 'ttsStart'
    | 'audioPlayback'
    | 'avatarUpdate';

export function createPipelineTimer() {
    const t0 = performance.now();
    const marks: Record<string, number> = { sent: t0 };

    return {
        mark(name: PipelineMark) {
            marks[name] = performance.now();
        },
        snapshot(): ClientPipelineTiming {
            const since = (name: string) =>
                Math.round((marks[name] ?? t0) - t0);
            return {
                messageSentMs: 0,
                metaReceivedMs: since('meta'),
                firstChunkMs: since('firstChunk'),
                doneReceivedMs: since('done'),
                ttsStartMs: since('ttsStart'),
                audioPlaybackMs: since('audioPlayback'),
                avatarUpdateMs: since('avatarUpdate'),
            };
        },
        logBreakdown(serverTiming?: Record<string, number>) {
            if (!IS_DEV) return;
            const c = this.snapshot();
            const fmt = (label: string, ms: number | undefined) =>
                `${label.padEnd(26)} .... ${(ms ?? 0).toFixed(0).padStart(6)} ms`;

            const lines = [
                fmt('Message sent (client)', c.messageSentMs),
                serverTiming?.ml_analysis_ms !== undefined
                    ? fmt('ML analysis', serverTiming.ml_analysis_ms)
                    : null,
                serverTiming?.intent_detection_ms !== undefined
                    ? fmt('Intent detection', serverTiming.intent_detection_ms)
                    : null,
                serverTiming?.pinecone_embed_ms !== undefined
                    ? fmt('Pinecone retrieval', (serverTiming.pinecone_embed_ms ?? 0)
                        + (serverTiming.pinecone_query_ms ?? 0)
                        + (serverTiming.memory_filtering_ms ?? 0))
                    : null,
                serverTiming?.prompt_construction_ms !== undefined
                    ? fmt('Prompt construction', serverTiming.prompt_construction_ms)
                    : null,
                fmt('Meta received', c.metaReceivedMs),
                serverTiming?.ollama_ttft_ms !== undefined
                    ? fmt('Ollama TTFT', serverTiming.ollama_ttft_ms)
                    : null,
                fmt('First chunk (client)', c.firstChunkMs),
                serverTiming?.ollama_generation_ms !== undefined
                    ? fmt('Ollama generation', serverTiming.ollama_generation_ms)
                    : null,
                fmt('Stream done (client)', c.doneReceivedMs),
                fmt('TTS generation', c.ttsStartMs > 0 ? c.ttsStartMs - c.doneReceivedMs : serverTiming?.tts_generation_ms),
                fmt('Audio playback start', c.audioPlaybackMs),
                fmt('Avatar update', c.avatarUpdateMs),
                fmt('Total (client)', c.audioPlaybackMs || c.doneReceivedMs),
            ].filter(Boolean);

            console.debug('[Pipeline Timing — Client]\n' + lines.join('\n'));
            if (serverTiming) {
                console.debug('[Pipeline Timing — Server]', serverTiming);
            }
        },
    };
}
