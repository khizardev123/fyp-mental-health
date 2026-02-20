"use client";
import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertTriangle, Brain, Heart, Zap, ChevronDown, ChevronRight, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ai, avatar } from '@/lib/api';
import Avatar from './Avatar';
import CrisisModal from './CrisisModal';

// ─── Types ─────────────────────────────────────────────────────────────────
interface ModelAnalysis {
    emotion: string;
    emotion_confidence: number;
    all_emotions: Record<string, number>;
    risk_level: string;
    crisis_probability: number;
    mental_state: string;
    mental_health_confidence: number;
    processing_time_ms: number;
}

interface Message {
    role: 'user' | 'avatar';
    text: string;
    analysis?: ModelAnalysis;    // ← attached to avatar messages
}

const EMOTION_EMOJI: Record<string, string> = {
    joy: '😊', sadness: '😢', anger: '😠',
    fear: '😨', love: '❤️', surprise: '😲',
    disgust: '😒', neutral: '😐',
};

const RISK_COLORS: Record<string, string> = {
    LOW: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    MEDIUM: 'text-yellow-400  bg-yellow-500/10  border-yellow-500/20',
    HIGH: 'text-orange-400  bg-orange-500/10  border-orange-500/20',
    CRISIS: 'text-red-400     bg-red-500/10     border-red-500/20',
};

const MODEL_COLORS: Record<string, string> = {
    LOW: '#22c55e',
    MEDIUM: '#eab308',
    HIGH: '#f97316',
    CRISIS: '#ef4444',
};

// ─── Model Analysis Dropdown (ChatGPT thinking style) ─────────────────────
function ModelAnalysisDropdown({ analysis }: { analysis: ModelAnalysis }) {
    const [open, setOpen] = useState(false);

    const topEmotions = Object.entries(analysis.all_emotions)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4);

    return (
        <div className="mt-2 rounded-lg border border-slate-700/60 overflow-hidden text-xs">
            {/* Toggle button */}
            <button
                onClick={() => setOpen(v => !v)}
                className="w-full flex items-center justify-between px-3 py-2 bg-slate-800/60 hover:bg-slate-800/90 transition-colors text-slate-400 hover:text-slate-200"
            >
                <span className="flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="font-medium text-slate-300">Model Analysis</span>
                    <span className="text-slate-500">• {analysis.processing_time_ms.toFixed(1)} ms</span>
                </span>
                <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
                    <ChevronDown className="w-3.5 h-3.5" />
                </motion.span>
            </button>

            {/* Expanded content */}
            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden bg-slate-900/60"
                    >
                        <div className="p-3 space-y-3">
                            {/* Emotion Model */}
                            <div>
                                <div className="flex items-center gap-1.5 text-indigo-400 font-semibold mb-1.5">
                                    <span>🧠</span> Emotion Classifier
                                </div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-slate-300">Primary:</span>
                                    <span className="font-bold text-white">
                                        {EMOTION_EMOJI[analysis.emotion] || '😐'} {analysis.emotion}
                                    </span>
                                    <span className="ml-auto text-slate-400">
                                        {(analysis.emotion_confidence * 100).toFixed(1)}% confidence
                                    </span>
                                </div>
                                <div className="space-y-1">
                                    {topEmotions.map(([em, prob]) => (
                                        <div key={em} className="flex items-center gap-2">
                                            <span className="w-16 text-slate-400 capitalize">{em}</span>
                                            <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${prob * 100}%` }}
                                                    transition={{ duration: 0.5, delay: 0.1 }}
                                                    className="h-full rounded-full"
                                                    style={{ background: em === analysis.emotion ? '#6366f1' : '#334155' }}
                                                />
                                            </div>
                                            <span className="text-slate-500 w-10 text-right">{(prob * 100).toFixed(1)}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="border-t border-slate-700/50" />

                            {/* Crisis Model */}
                            <div>
                                <div className="flex items-center gap-1.5 text-rose-400 font-semibold mb-1.5">
                                    <span>🔴</span> Crisis Detector
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="flex-1">
                                        <div className="flex justify-between mb-1">
                                            <span className="text-slate-400">Crisis probability</span>
                                            <span className="font-bold" style={{ color: MODEL_COLORS[analysis.risk_level] }}>
                                                {(analysis.crisis_probability * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${analysis.crisis_probability * 100}%` }}
                                                transition={{ duration: 0.5, delay: 0.2 }}
                                                className="h-full rounded-full"
                                                style={{ background: MODEL_COLORS[analysis.risk_level] }}
                                            />
                                        </div>
                                    </div>
                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${RISK_COLORS[analysis.risk_level]}`}>
                                        {analysis.risk_level}
                                    </span>
                                </div>
                            </div>

                            <div className="border-t border-slate-700/50" />

                            {/* Mental Health Model */}
                            <div>
                                <div className="flex items-center gap-1.5 text-purple-400 font-semibold mb-1.5">
                                    <span>💭</span> Mental Health Classifier
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-300">Detected state:</span>
                                    <span className="font-bold text-white capitalize">{analysis.mental_state}</span>
                                </div>
                                <div className="flex items-center justify-between mt-1">
                                    <span className="text-slate-400">Confidence</span>
                                    <span className="text-purple-300">{(analysis.mental_health_confidence * 100).toFixed(1)}%</span>
                                </div>
                                <div className="mt-1.5 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${analysis.mental_health_confidence * 100}%` }}
                                        transition={{ duration: 0.5, delay: 0.3 }}
                                        className="h-full rounded-full bg-purple-500"
                                    />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// ─── Main JournalArea ──────────────────────────────────────────────────────
export default function JournalArea({
    onNewEntry,
}: {
    onNewEntry?: (entry: { emotion: string; confidence: number; crisis_prob: number; mental_state: string }) => void;
}) {
    const [content, setContent] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [currentEmotion, setCurrentEmotion] = useState('neutral');
    const [currentRisk, setCurrentRisk] = useState('LOW');
    const [showCrisis, setShowCrisis] = useState(false);
    const [conversationHistory, setConversationHistory] = useState<any[]>([]);
    const [error, setError] = useState<string | null>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // WhatsApp style: immediate scroll + slight delay for animations
        const scrollToBottom = () => {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        };
        scrollToBottom();
        const timer = setTimeout(scrollToBottom, 200);
        return () => clearTimeout(timer);
    }, [messages, isAnalyzing]); // Scroll on new messages OR when thinking starts/ends

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit();
    };

    const handleSubmit = async () => {
        if (!content.trim() || isAnalyzing) return;
        const userText = content.trim();
        setContent('');
        setError(null);
        setIsAnalyzing(true);
        setMessages(prev => [...prev, { role: 'user', text: userText }]);

        try {
            // ── Step 1: AI Analysis (context-aware with history) ──
            const analysisRes = await ai.analyze(userText, conversationHistory);
            const { emotion: emoData, crisis: crisisData, mental_health: mhData, processing_time_ms } = analysisRes.data;

            setCurrentEmotion(emoData.emotion);
            setCurrentRisk(crisisData.risk_level);

            if (crisisData.risk_level === 'HIGH' || crisisData.risk_level === 'CRISIS') {
                setShowCrisis(true);
            }

            const analysis: ModelAnalysis = {
                emotion: emoData.emotion,
                emotion_confidence: emoData.confidence,
                all_emotions: emoData.all_emotions || {},
                risk_level: crisisData.risk_level,
                crisis_probability: crisisData.crisis_probability,
                mental_state: mhData?.mental_state || 'normal',
                mental_health_confidence: mhData?.confidence || 0,
                processing_time_ms: processing_time_ms || 0,
            };

            // Notify parent for analytics panel update
            onNewEntry?.({
                emotion: emoData.emotion,
                confidence: emoData.confidence,
                crisis_prob: crisisData.crisis_probability,
                mental_state: mhData?.mental_state || 'normal',
            });

            // ── Step 2: Avatar Response (ML-driven) ──
            const avatarRes = await avatar.respond({
                journal_text: userText,
                emotion: emoData.emotion,
                confidence: emoData.confidence,
                risk_level: crisisData.risk_level,
                crisis_probability: crisisData.crisis_probability,
                mental_state: mhData?.mental_state || 'normal',
                mental_health_confidence: mhData?.confidence || 0,
                conversation_history: conversationHistory,
            });

            const avatarText = avatarRes.data.text;

            setMessages(prev => [...prev, {
                role: 'avatar',
                text: avatarText,
                analysis,  // ← attach for dropdown
            }]);

            setConversationHistory(prev => [
                ...prev,
                { role: 'user', content: userText },
                { role: 'assistant', content: avatarText },
            ]);
        } catch (err: any) {
            console.error('Analysis error:', err);
            const errMsg = err?.response?.data?.detail || err?.message || 'Connection error';
            setError(errMsg);
            setMessages(prev => [...prev, {
                role: 'avatar',
                text: "Your words matter to me. I'm having a brief connection issue — please try again in a moment. 💙",
            }]);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const riskStyle = RISK_COLORS[currentRisk] || RISK_COLORS.LOW;
    const emotionEmoji = EMOTION_EMOJI[currentEmotion] || '😐';

    return (
        <div className="flex flex-col h-full gap-3 overflow-hidden" style={{ maxHeight: '100%' }}>
            {/* Avatar + Status */}
            <div className="flex-shrink-0 flex items-center gap-3 p-3 bg-slate-800/50 rounded-2xl border border-slate-700/50">
                <Avatar emotion={currentEmotion} isThinking={isAnalyzing} />
                <div className="flex-1 min-w-0">
                    <h2 className="text-base font-bold text-white">SereneMind</h2>
                    <p className="text-xs text-slate-400">Your empathetic AI companion</p>
                    {messages.length > 0 && (
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                            <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-indigo-300">
                                <Brain className="w-2.5 h-2.5" />
                                {emotionEmoji} {currentEmotion}
                            </span>
                            <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 border rounded-full ${riskStyle}`}>
                                <Zap className="w-2.5 h-2.5" />
                                {currentRisk}
                            </span>
                        </div>
                    )}
                </div>
                {isAnalyzing && (
                    <div className="flex items-center gap-1.5 text-indigo-300 text-xs flex-shrink-0">
                        <Activity className="w-3.5 h-3.5 animate-pulse" />
                        <span>Analysing...</span>
                    </div>
                )}
            </div>

            {/* Messages Area - WhatsApp Style Scroll */}
            <div
                className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col gap-3 pr-1 min-h-0 scroll-smooth"
                style={{
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#4f46e5 #1e293b',
                    flexBasis: '0px'
                }}
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
                            Share how you're feeling. Three AI models will analyse your entry in real-time and SereneMind will respond with empathy.
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
                                        {msg.text}
                                    </div>
                                    {/* Model Analysis Dropdown — only on avatar messages */}
                                    {msg.role === 'avatar' && msg.analysis && (
                                        <ModelAnalysisDropdown analysis={msg.analysis} />
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {/* Typing indicator */}
                {isAnalyzing && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex-shrink-0 flex items-center justify-center mr-2 mt-1">
                            <Heart className="w-3.5 h-3.5 text-white" />
                        </div>
                        <div className="bg-slate-800/80 border border-slate-700 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-1.5">
                            {[0, 150, 300].map(delay => (
                                <span key={delay} className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                            ))}
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Error */}
            {error && (
                <div className="flex items-center gap-2 text-xs text-orange-300 bg-orange-500/10 border border-orange-500/20 rounded-lg p-2 px-3">
                    <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                    <span>{error}</span>
                </div>
            )}

            {/* Input - Sticky at bottom */}
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
                        {isAnalyzing ? 'Reflecting...' : 'Share'}
                    </button>
                </div>
            </div>

            {showCrisis && <CrisisModal onClose={() => setShowCrisis(false)} />}
        </div>
    );
}
