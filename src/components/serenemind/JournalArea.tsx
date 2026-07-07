"use client";
import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertTriangle, Brain, Heart, Zap, ChevronDown, Activity, Tag, Shield, Star, Camera, Volume2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { chat } from '@/lib/serenemind/api';
import Avatar from './Avatar';
import CrisisModal from './CrisisModal';
import { normalizeAvatarEmotion, isStressEmotion } from '@/lib/serenemind/emotionFusion';
import { useAvatarSpeech } from '@/hooks/serenemind/useAvatarSpeech';
import { useMediaPipeFaceMesh } from '@/hooks/serenemind/useMediaPipeFaceMesh';
import { useStreamBuffer } from '@/hooks/serenemind/useStreamBuffer';
import { createPipelineTimer } from '@/lib/serenemind/pipelineTiming';
import FaceTrackingDebugOverlay from './FaceTrackingDebugOverlay';
import { inferFaceEmotionFromSignals } from '@/lib/serenemind/faceEmotionInference';

// ─── Unified Model Analysis Types ───────────────────────────────────────────
interface UnifiedAnalysis {
    // Core
    mental_state: string;
    raw_label: string;
    emotion: string;
    // Crisis
    crisis_risk: string;           // LOW | MEDIUM | HIGH | CRISIS
    crisis_probability: number;
    requires_immediate_action: boolean;
    // New unified fields
    severity_rating: number;       // 1–10
    tags: string[];
    confidence: number;
    all_scores: Record<string, number>;
    semantic_summary: string;
    triggered_by: string;
    // Meta
    processing_time_ms: number;
    model_version: string;
    emotion_rules_applied?: string[];
    ml_raw_label?: string;
    assessment?: string;
    text_emotion?: string;
    face_emotion?: string | null;
    face_confidence?: number;
    fusion_active?: boolean;
    fusion_note?: string | null;
}

interface Message {
    role: 'user' | 'avatar';
    text: string;
    analysis?: UnifiedAnalysis;
}

// ─── Emoji & color maps ──────────────────────────────────────────────────────
const EMOTION_EMOJI: Record<string, string> = {
    sadness: '😢', joy: '😊', anger: '😠',
    fear: '😨', neutral: '😐', love: '❤️', surprise: '😲',
    stress: '😰', anxiety: '😟',
};
const STATE_EMOJI: Record<string, string> = {
    depression: '🌧️', anxiety: '⚡', stress: '🔥', grief: '🕊️',
    anger: '🌋', joy: '☀️', fear: '🌑', crisis: '🚨', normal: '✅', stable: '✅',
};
const RISK_COLORS: Record<string, string> = {
    LOW: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    MEDIUM: 'text-yellow-400  bg-yellow-500/10  border-yellow-500/20',
    HIGH: 'text-orange-400  bg-orange-500/10  border-orange-500/20',
    CRISIS: 'text-red-400     bg-red-500/10     border-red-500/20',
};
const RISK_BAR_COLOR: Record<string, string> = {
    LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRISIS: '#ef4444',
};
const SEVERITY_COLOR = (s: number) => {
    if (s <= 3) return '#22c55e';
    if (s <= 5) return '#84cc16';
    if (s <= 7) return '#f97316';
    return '#ef4444';
};

// ─── Model Analysis Dropdown (Expanded unified output) ───────────────────────
function ModelAnalysisDropdown({ analysis }: { analysis: UnifiedAnalysis }) {
    const [open, setOpen] = useState(false);
    const topScores = Object.entries(analysis.all_scores)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    return (
        <div className="mt-2 rounded-lg border border-slate-700/60 overflow-hidden text-xs">
            {/* Toggle */}
            <button
                onClick={() => setOpen(v => !v)}
                className="w-full flex items-center justify-between px-3 py-2 bg-slate-800/60 hover:bg-slate-800/90 transition-colors text-slate-400 hover:text-slate-200"
            >
                <span className="flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="font-medium text-slate-300">Unified AI Analysis</span>
                    <span className="text-slate-500">• {analysis.processing_time_ms.toFixed(1)} ms</span>
                    <span className="ml-1 text-[9px] px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-full border border-indigo-500/30">
                        v{analysis.model_version || '2.0'}
                    </span>
                </span>
                <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
                    <ChevronDown className="w-3.5 h-3.5" />
                </motion.span>
            </button>

            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden bg-slate-900/60"
                    >
                        <div className="p-3 space-y-4">

                            {/* ── Severity Meter ── */}
                            <div>
                                <div className="flex items-center justify-between mb-1.5">
                                    <span className="flex items-center gap-1.5 text-orange-400 font-semibold">
                                        <Star className="w-3 h-3" /> Severity Rating
                                    </span>
                                    <span className="font-bold text-white text-sm">
                                        {analysis.severity_rating}<span className="text-slate-500 text-xs">/10</span>
                                    </span>
                                </div>
                                <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${analysis.severity_rating * 10}%` }}
                                        transition={{ duration: 0.6, ease: 'easeOut' }}
                                        className="h-full rounded-full"
                                        style={{ background: SEVERITY_COLOR(analysis.severity_rating) }}
                                    />
                                </div>
                                <div className="flex justify-between text-[9px] text-slate-600 mt-0.5">
                                    <span>Minimal</span><span>Moderate</span><span>Severe</span>
                                </div>
                            </div>

                            <div className="border-t border-slate-700/50" />

                            {/* ── Mental State + Emotion ── */}
                            <div>
                                <div className="flex items-center gap-1.5 text-purple-400 font-semibold mb-2">
                                    <span>🧠</span> Unified Mental Health Model
                                </div>
                                <div className="grid grid-cols-2 gap-2 mb-2">
                                    <div className="bg-slate-800/50 rounded-lg p-2 border border-slate-700/40">
                                        <div className="text-slate-500 text-[10px] mb-0.5">Mental State</div>
                                        <div className="font-bold text-white flex items-center gap-1">
                                            {STATE_EMOJI[analysis.raw_label] || '💭'} {analysis.mental_state}
                                        </div>
                                    </div>
                                    <div className="bg-slate-800/50 rounded-lg p-2 border border-slate-700/40">
                                        <div className="text-slate-500 text-[10px] mb-0.5">Emotion</div>
                                        <div className="font-bold text-white flex items-center gap-1">
                                            {EMOTION_EMOJI[analysis.emotion] || '😐'} {analysis.emotion}
                                        </div>
                                    </div>
                                </div>
                                {/* All class scores */}
                                <div className="space-y-1">
                                    {topScores.map(([cls, prob]) => (
                                        <div key={cls} className="flex items-center gap-2">
                                            <span className="w-16 text-slate-400 capitalize text-[10px]">{cls}</span>
                                            <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${prob * 100}%` }}
                                                    transition={{ duration: 0.5, delay: 0.05 }}
                                                    className="h-full rounded-full"
                                                    style={{ background: cls === analysis.raw_label ? '#6366f1' : '#334155' }}
                                                />
                                            </div>
                                            <span className="text-slate-500 w-9 text-right text-[10px]">
                                                {(prob * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    ))}
                                </div>
                                <div className="flex items-center justify-between mt-2 text-[10px]">
                                    <span className="text-slate-500">Confidence</span>
                                    <span className="text-indigo-300 font-semibold">
                                        {(analysis.confidence * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>

                            <div className="border-t border-slate-700/50" />

                            {/* ── Crisis Risk ── */}
                            <div>
                                <div className="flex items-center gap-1.5 text-rose-400 font-semibold mb-2">
                                    <Shield className="w-3 h-3" /> Crisis Assessment
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="flex-1">
                                        <div className="flex justify-between mb-1">
                                            <span className="text-slate-400 text-[10px]">Crisis probability</span>
                                            <span className="font-bold text-[10px]" style={{ color: RISK_BAR_COLOR[analysis.crisis_risk] }}>
                                                {(analysis.crisis_probability * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${analysis.crisis_probability * 100}%` }}
                                                transition={{ duration: 0.5, delay: 0.2 }}
                                                className="h-full rounded-full"
                                                style={{ background: RISK_BAR_COLOR[analysis.crisis_risk] }}
                                            />
                                        </div>
                                    </div>
                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border flex-shrink-0 ${RISK_COLORS[analysis.crisis_risk]}`}>
                                        {analysis.crisis_risk}
                                    </span>
                                </div>
                            </div>

                            <div className="border-t border-slate-700/50" />

                            {/* ── Contextual Tags ── */}
                            {analysis.tags?.length > 0 && (
                                <div>
                                    <div className="flex items-center gap-1.5 text-teal-400 font-semibold mb-2">
                                        <Tag className="w-3 h-3" /> Semantic Tags
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {analysis.tags.map(tag => (
                                            <span key={tag} className="text-[10px] px-2 py-0.5 bg-teal-500/10 border border-teal-500/20 text-teal-300 rounded-full capitalize">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* ── Semantic Summary ── */}
                            {analysis.emotion_rules_applied && analysis.emotion_rules_applied.length > 0 && (
                                <div className="text-[10px] text-purple-300/80">
                                    Rules: {analysis.emotion_rules_applied.join(', ')}
                                </div>
                            )}
                            {analysis.semantic_summary && (
                                <div className="bg-slate-800/40 rounded-lg p-2.5 border border-slate-700/30">
                                    <div className="text-slate-500 text-[10px] mb-1 font-medium">📋 AI Assessment</div>
                                    <p className="text-slate-300 text-[11px] leading-relaxed">{analysis.semantic_summary}</p>
                                </div>
                            )}

                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// ─── Main JournalArea ────────────────────────────────────────────────────────
export default function JournalArea({
    onNewEntry,
}: {
    onNewEntry?: (entry: {
        emotion: string; confidence: number; crisis_prob: number;
        mental_state: string; severity: number; tags: string[];
        text_emotion?: string;
        face_emotion?: string | null;
        final_avatar_emotion?: string;
        is_stress?: boolean;
    }) => void;
}) {
    const [content, setContent] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [textEmotion, setTextEmotion] = useState('neutral');
    const [faceEmotion, setFaceEmotion] = useState<string | null>(null);
    const [faceConfidence, setFaceConfidence] = useState(0);
    const [finalAvatarEmotion, setFinalAvatarEmotion] = useState('neutral');
    const [currentRisk, setCurrentRisk] = useState('LOW');
    const [currentSeverity, setCurrentSeverity] = useState(0);
    const [showCrisis, setShowCrisis] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [ttsEnabled, setTtsEnabled] = useState(true);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const activeStreamRef = useRef(0);
    const avatarMsgIndexRef = useRef(-1);

    const { speakText, stopSpeech, resetSpeakDedup, isSpeaking, mouthOpen } = useAvatarSpeech();
    const streamBuffer = useStreamBuffer();
    const {
        faceTracking,
        trackingEnabled,
        setTrackingEnabled,
        initialized,
        error: faceTrackingError,
        videoRef,
        landmarksRef,
    } = useMediaPipeFaceMesh(false);

    useEffect(() => {
        setFinalAvatarEmotion(normalizeAvatarEmotion(textEmotion));
    }, [textEmotion]);

    const getUserId = () => {
        if (typeof window === 'undefined') return 'demo-user';
        try {
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            return user.id || 'demo-user';
        } catch {
            return 'demo-user';
        }
    };

    useEffect(() => {
        const storedSession = localStorage.getItem('session_id');
        if (!storedSession) return;

        setSessionId(storedSession);
        chat.getHistory(storedSession)
            .then(res => {
                const loaded = res.data.messages as Message[];
                if (loaded.length > 0) {
                    setMessages(loaded);
                    const lastAnalysis = [...loaded].reverse().find(m => m.analysis)?.analysis;
                    if (lastAnalysis) {
                        setTextEmotion(lastAnalysis.emotion);
                        setCurrentRisk(lastAnalysis.crisis_risk);
                        setCurrentSeverity(lastAnalysis.severity_rating);
                    }
                }
            })
            .catch(() => {
                // Session may have expired — start fresh
                localStorage.removeItem('session_id');
            });
    }, []);

    useEffect(() => {
        const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        scrollToBottom();
        const t = setTimeout(scrollToBottom, 200);
        return () => clearTimeout(t);
    }, [messages, isAnalyzing]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit();
    };

    const applySideEffects = (data: Record<string, any>) => {
        localStorage.setItem('session_id', data.session_id as string);
        setSessionId(data.session_id as string);

        const raw = (data.analysis || {}) as UnifiedAnalysis;
        const emotionVal = typeof raw.emotion === 'string' ? raw.emotion : 'neutral';
        const unified: UnifiedAnalysis = {
            mental_state: raw.mental_state,
            raw_label: raw.raw_label,
            emotion: emotionVal,
            crisis_risk: raw.crisis_risk || (data.crisis as string) || 'LOW',
            crisis_probability: raw.crisis_probability ?? 0,
            requires_immediate_action: raw.requires_immediate_action ?? false,
            severity_rating: raw.severity_rating,
            tags: raw.tags || [],
            confidence: raw.confidence ?? 0,
            all_scores: raw.all_scores || {},
            semantic_summary: raw.semantic_summary || raw.assessment || '',
            triggered_by: raw.triggered_by || 'model',
            processing_time_ms: raw.processing_time_ms || 0,
            model_version: raw.model_version || '4.0.0',
            emotion_rules_applied: raw.emotion_rules_applied,
            ml_raw_label: raw.ml_raw_label,
            assessment: raw.assessment,
            text_emotion: raw.text_emotion,
            face_emotion: raw.face_emotion,
            face_confidence: raw.face_confidence,
            fusion_active: raw.fusion_active,
            fusion_note: raw.fusion_note,
        };

        setTextEmotion(unified.emotion);
        setFaceEmotion(unified.face_emotion ?? (data.face_emotion as string | null) ?? null);
        setFaceConfidence(unified.face_confidence ?? (data.face_confidence as number) ?? 0);
        setFinalAvatarEmotion(normalizeAvatarEmotion(unified.emotion));
        setCurrentRisk(unified.crisis_risk);
        setCurrentSeverity(unified.severity_rating);

        if (data.show_crisis) setShowCrisis(true);

        const textNorm = normalizeAvatarEmotion(unified.text_emotion || unified.emotion);
        const faceNorm = unified.face_emotion ? normalizeAvatarEmotion(unified.face_emotion) : null;

        onNewEntry?.({
            emotion: unified.emotion,
            confidence: unified.confidence,
            crisis_prob: unified.crisis_probability,
            mental_state: unified.mental_state,
            severity: unified.severity_rating,
            tags: unified.tags,
            text_emotion: textNorm,
            face_emotion: faceNorm,
            final_avatar_emotion: textNorm,
            is_stress: isStressEmotion(unified.emotion) || isStressEmotion(unified.mental_state),
        });

        return unified;
    };

    const updateStreamingText = (text: string, streamId: number) => {
        if (streamId !== activeStreamRef.current) return;
        const idx = avatarMsgIndexRef.current;
        if (idx < 0) return;
        setMessages(prev => {
            if (idx >= prev.length || prev[idx].role !== 'avatar') return prev;
            const updated = [...prev];
            updated[idx] = { ...updated[idx], text };
            return updated;
        });
    };

    const finalizeAvatarMessage = (
        data: Record<string, any>,
        replyText: string,
        streamId: number,
    ) => {
        if (streamId !== activeStreamRef.current) return;
        const unified = applySideEffects(data);
        const idx = avatarMsgIndexRef.current;

        setMessages(prev => {
            if (idx >= 0 && idx < prev.length && prev[idx].role === 'avatar') {
                const updated = [...prev];
                updated[idx] = { ...updated[idx], text: replyText, analysis: unified };
                return updated;
            }
            const updated = [...prev];
            for (let i = updated.length - 1; i >= 0; i--) {
                if (updated[i].role === 'avatar') {
                    updated[i] = { ...updated[i], text: replyText, analysis: unified };
                    return updated;
                }
            }
            updated.push({ role: 'avatar', text: replyText, analysis: unified });
            return updated;
        });

        avatarMsgIndexRef.current = -1;
    };

    const handleSubmit = async () => {
        if (!content.trim() || isAnalyzing) return;
        const userText = content.trim();
        setContent('');
        setError(null);
        setIsAnalyzing(true);
        const streamId = ++activeStreamRef.current;
        stopSpeech();
        resetSpeakDedup();
        streamBuffer.reset();
        avatarMsgIndexRef.current = -1;

        setMessages(prev => {
            avatarMsgIndexRef.current = prev.length + 1;
            return [
                ...prev,
                { role: 'user', text: userText },
                { role: 'avatar', text: '' },
            ];
        });

        let gotFirstChunk = false;
        const pipelineTimer = createPipelineTimer();

        const inferred = trackingEnabled && faceTracking.faceDetected
            ? inferFaceEmotionFromSignals(faceTracking)
            : { emotion: 'neutral', confidence: 0 };
        const sendFace = inferred.confidence > 0 ? inferred.emotion : undefined;

        try {
            await chat.sendMessageStream(
                {
                    session_id: sessionId || undefined,
                    message: userText,
                    face_emotion: sendFace,
                    face_confidence: inferred.confidence,
                },
                {
                    onMeta: (data) => {
                        if (streamId !== activeStreamRef.current) return;
                        pipelineTimer.mark('meta');
                        if (data.session_id) {
                            localStorage.setItem('session_id', data.session_id as string);
                            setSessionId(data.session_id as string);
                        }
                    },
                    onChunk: (chunk) => {
                        if (streamId !== activeStreamRef.current) return;
                        if (!gotFirstChunk) {
                            gotFirstChunk = true;
                            pipelineTimer.mark('firstChunk');
                            setIsAnalyzing(false);
                        }
                        streamBuffer.appendChunk(chunk, (text) => updateStreamingText(text, streamId));
                    },
                    onDone: (data) => {
                        if (streamId !== activeStreamRef.current) return;
                        pipelineTimer.mark('done');
                        const replyText = (data.reply || data.text || '') as string;
                        streamBuffer.setFinal(replyText);
                        streamBuffer.flushNow((text) => updateStreamingText(text, streamId));
                        finalizeAvatarMessage(data, replyText, streamId);
                        pipelineTimer.mark('avatarUpdate');
                        const serverTiming = data.pipeline_timing as Record<string, number> | undefined;
                        pipelineTimer.logBreakdown(serverTiming);
                        if (ttsEnabled && replyText.trim()) {
                            requestAnimationFrame(() => {
                                requestAnimationFrame(() => {
                                    if (streamId === activeStreamRef.current) {
                                        pipelineTimer.mark('ttsStart');
                                        speakText(replyText, {
                                            onAudioStart: () => pipelineTimer.mark('audioPlayback'),
                                            onComplete: () => {
                                                pipelineTimer.logBreakdown(serverTiming);
                                            },
                                        });
                                    }
                                });
                            });
                        }
                    },
                },
            );
        } catch (err: any) {
            console.error('Analysis error:', err);
            const detail = err?.message;
            let errMsg = 'Connection error — is the AI service running?';
            if (typeof detail === 'string' && detail.length < 200) errMsg = detail;

            setError(errMsg);
            setMessages(prev => {
                const idx = avatarMsgIndexRef.current;
                const fallback = "Your words matter to me. I'm having a brief connection issue — please try again in a moment. 💙";
                if (idx >= 0 && idx < prev.length && prev[idx].role === 'avatar') {
                    const updated = [...prev];
                    updated[idx] = { role: 'avatar', text: fallback };
                    return updated;
                }
                const withoutEmpty = prev.filter((m, i) => !(i === prev.length - 1 && m.role === 'avatar' && !m.text));
                return [...withoutEmpty, { role: 'avatar', text: fallback }];
            });
            avatarMsgIndexRef.current = -1;
        } finally {
            setIsAnalyzing(false);
        }
    };

    const riskStyle = RISK_COLORS[currentRisk] || RISK_COLORS.LOW;
    const emotionEmoji = EMOTION_EMOJI[textEmotion] || EMOTION_EMOJI[finalAvatarEmotion] || '😐';

    return (
        <div className="flex flex-col h-full gap-3 overflow-hidden" style={{ maxHeight: '100%' }}>
            {/* Webcam: visible in dev overlay, hidden in production */}
            {process.env.NODE_ENV !== 'development' && trackingEnabled && (
                <video ref={videoRef} className="hidden" muted playsInline autoPlay />
            )}
            <FaceTrackingDebugOverlay
                active={trackingEnabled}
                videoRef={videoRef}
                landmarksRef={landmarksRef}
                tracking={faceTracking}
                textEmotion={textEmotion}
                faceEmotion={faceEmotion}
                faceConfidence={faceConfidence}
            />

            {/* Avatar + Status bar */}
            <div className="flex-shrink-0 flex items-center gap-3 p-3 bg-slate-800/50 rounded-2xl border border-slate-700/50">
                <Avatar
                    emotion={finalAvatarEmotion}
                    isThinking={isAnalyzing}
                    mouthOpen={mouthOpen}
                    isSpeaking={isSpeaking}
                    faceTracking={trackingEnabled ? faceTracking : null}
                />
                <div className="flex-1 min-w-0">
                    <h2 className="text-base font-bold text-white">SereneMind</h2>
                    <p className="text-xs text-slate-400">Avatar · TTS · Memory-aware</p>
                    {messages.length > 0 && (
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                            <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-indigo-300">
                                <Brain className="w-2.5 h-2.5" />
                                Text: {emotionEmoji} {normalizeAvatarEmotion(textEmotion)}
                            </span>
                            {trackingEnabled && initialized && faceTracking.faceDetected && (
                                <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-300">
                                    <Camera className="w-2.5 h-2.5" />
                                    Face: {faceEmotion || '—'} ({(faceConfidence * 100).toFixed(0)}%)
                                </span>
                            )}
                            {trackingEnabled && initialized && !faceTracking.faceDetected && (
                                <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-slate-700/50 border border-slate-600/40 rounded-full text-slate-400">
                                    <Camera className="w-2.5 h-2.5" />
                                    No face
                                </span>
                            )}
                            {faceTrackingError && (
                                <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-300" title={faceTrackingError}>
                                    <Camera className="w-2.5 h-2.5" />
                                    Camera off
                                </span>
                            )}
                            <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-300">
                                Avatar: {normalizeAvatarEmotion(finalAvatarEmotion)}
                            </span>
                            <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 border rounded-full ${riskStyle}`}>
                                <Zap className="w-2.5 h-2.5" />
                                {currentRisk}
                            </span>
                            {currentSeverity > 0 && (
                                <span
                                    className="flex items-center gap-1 text-[10px] px-2 py-0.5 border rounded-full"
                                    style={{
                                        color: SEVERITY_COLOR(currentSeverity),
                                        borderColor: SEVERITY_COLOR(currentSeverity) + '40',
                                        background: SEVERITY_COLOR(currentSeverity) + '15',
                                    }}
                                >
                                    <Star className="w-2.5 h-2.5" />
                                    Severity {currentSeverity}/10
                                </span>
                            )}
                        </div>
                    )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                        type="button"
                        onClick={() => setTtsEnabled(v => !v)}
                        className={`p-1.5 rounded-lg border text-xs ${ttsEnabled ? 'border-emerald-500/30 text-emerald-300' : 'border-slate-600 text-slate-500'}`}
                        title="Toggle voice"
                    >
                        <Volume2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                        type="button"
                        onClick={() => setTrackingEnabled(v => !v)}
                        className={`p-1.5 rounded-lg border text-xs ${trackingEnabled ? 'border-purple-500/30 text-purple-300' : 'border-slate-600 text-slate-500'}`}
                        title="Toggle face tracking (MediaPipe)"
                    >
                        <Camera className="w-3.5 h-3.5" />
                    </button>
                    {isAnalyzing && (
                        <div className="flex items-center gap-1.5 text-indigo-300 text-xs">
                            <Activity className="w-3.5 h-3.5 animate-pulse" />
                            <span>Analysing...</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Messages Area */}
            <div
                className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col gap-3 pr-1 min-h-0 scroll-smooth"
                style={{ scrollbarWidth: 'thin', scrollbarColor: '#4f46e5 #1e293b', flexBasis: '0px' }}
            >
                {messages.length === 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex flex-col items-center justify-center h-full text-center px-6"
                    >
                        <span className="text-5xl mb-3">💙</span>
                        <h3 className="text-lg font-semibold text-slate-200 mb-1">This is your safe space</h3>
                        <p className="text-slate-400 text-xs leading-relaxed max-w-xs">
                            Share how you're feeling or just say hello. SereneMind remembers your conversation and supports you naturally.
                        </p>
                    </motion.div>
                )}

                <AnimatePresence initial={false}>
                    {messages.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                {msg.role === 'avatar' && (
                                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex-shrink-0 flex items-center justify-center mr-2 mt-1">
                                        <Heart className="w-3.5 h-3.5 text-white" />
                                    </div>
                                )}
                                <div className={`max-w-[82%] ${msg.role === 'user' ? 'w-full flex flex-col items-end' : ''}`}>
                                    <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                                        ? 'bg-indigo-600 text-white rounded-br-sm'
                                        : 'bg-slate-800/80 border border-slate-700 text-slate-200 rounded-bl-sm'
                                        }`}>
                                        {msg.role === 'avatar' && !msg.text && isAnalyzing ? (
                                            <span className="flex items-center gap-1.5">
                                                {[0, 150, 300].map(delay => (
                                                    <span key={delay} className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                                                ))}
                                            </span>
                                        ) : (
                                            msg.text
                                        )}
                                    </div>
                                    {/* Unified Model Analysis Dropdown — avatar messages only */}
                                    {msg.role === 'avatar' && msg.analysis && (
                                        <ModelAnalysisDropdown analysis={msg.analysis} />
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                <div ref={messagesEndRef} />
            </div>

            {/* Error */}
            {error && (
                <div className="flex items-center gap-2 text-xs text-orange-300 bg-orange-500/10 border border-orange-500/20 rounded-lg p-2 px-3">
                    <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                    <span>{error}</span>
                </div>
            )}

            {/* Input */}
            <div className="flex-shrink-0 bg-slate-800/40 rounded-xl border border-slate-700/50 p-3 flex flex-col gap-2 focus-within:border-indigo-500/50 transition-all">
                <textarea
                    ref={textareaRef}
                    value={content}
                    onChange={e => setContent(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="What's on your mind today? (Ctrl+Enter to send)"
                    rows={3}
                    className="bg-transparent border-none resize-none focus:outline-none text-sm text-slate-200 placeholder:text-slate-500 w-full"
                />
                <div className="flex justify-between items-center border-t border-slate-700/40 pt-2">
                    <span className="text-xs text-slate-500">{content.length} chars • 🔒 Encrypted</span>
                    <button
                        onClick={handleSubmit}
                        disabled={!content.trim() || isAnalyzing}
                        className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white px-5 py-1.5 rounded-lg font-semibold flex items-center gap-2 transition-all text-sm"
                    >
                        {isAnalyzing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                        {isAnalyzing ? 'Analysing...' : 'Share'}
                    </button>
                </div>
            </div>

            {showCrisis && <CrisisModal onClose={() => setShowCrisis(false)} />}
        </div>
    );
}
