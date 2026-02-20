"use client";
import { useState } from 'react';
import { BarChart2, TrendingUp, PieChart, Cpu, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LineChart, Line, BarChart, Bar, RadarChart, Radar,
    PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

// ─── Types ────────────────────────────────────────────────────────────────────
interface AnalyticsEntry {
    label: string;
    crisis_prob: number;
    emotion: string;
    confidence: number;
    mental_state: string;
}

interface Props {
    entries?: AnalyticsEntry[];
    totalEntries?: number;
}

// ─── Colour maps ──────────────────────────────────────────────────────────────
const MENTAL_COLORS: Record<string, string> = {
    normal: '#22c55e',
    stable: '#22c55e',
    anxiety: '#a78bfa',
    depression: '#60a5fa',
    stress: '#fb923c',
    grief: '#f87171',
    anger: '#facc15',
};

// ─── Tab config ───────────────────────────────────────────────────────────────
const TABS = [
    { id: 'trends', label: 'Trends', Icon: TrendingUp },
    { id: 'insights', label: 'Insights', Icon: BarChart2 },
    { id: 'dist', label: 'Distribution', Icon: PieChart },
    { id: 'training', label: 'Training Metrics', Icon: Cpu },
];

// ─── Fixed training metrics (from our actual model evaluation) ───────────────
const TRAINING_RADAR = [
    { metric: 'Emotion Acc', A: 87 },
    { metric: 'Crisis AUC', A: 97 },
    { metric: 'MH Precision', A: 98 },
    { metric: 'F1 Score', A: 86 },
    { metric: 'Recall', A: 90 },
];
const MODEL_INFO = [
    { name: 'Emotion Classifier', algo: 'TF-IDF + LogReg', accuracy: '86.7%', size: '2.3 MB', latency: '~5 ms' },
    { name: 'Crisis Detector', algo: 'TF-IDF + Calib.', accuracy: '93.3%', size: '1.6 MB', latency: '~4 ms' },
    { name: 'Mental Health Model', algo: 'TF-IDF + LogReg', accuracy: '98.3%', size: '1.1 MB', latency: '~3 ms' },
];

// ─── Custom tooltip ───────────────────────────────────────────────────────────
const Tip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs shadow-xl">
            <p className="text-slate-400 mb-1">{label}</p>
            {payload.map((p: any) => (
                <p key={p.name} style={{ color: p.color }}>
                    {p.name}: {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}
                </p>
            ))}
        </div>
    );
};

// ─── Empty state ──────────────────────────────────────────────────────────────
function EmptyState({ label }: { label: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-10 text-center">
            <Activity className="w-8 h-8 text-slate-600 mb-2" />
            <p className="text-slate-500 text-xs">No data yet</p>
            <p className="text-slate-600 text-[10px] mt-1">Submit a journal entry to see {label}</p>
        </div>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function AnalyticsPanel({ entries = [], totalEntries }: Props) {
    const [activeTab, setActiveTab] = useState('trends');

    const hasData = entries.length > 0;

    // ── Trend data (real-time only)
    const trendData = entries.map(e => ({
        name: e.label,
        'Crisis Prob': +e.crisis_prob.toFixed(3),
        'Confidence': +e.confidence.toFixed(3),
    }));

    // ── Emotion frequency
    const emotionFreq: Record<string, number> = {};
    entries.forEach(e => { emotionFreq[e.emotion] = (emotionFreq[e.emotion] || 0) + 1; });
    const emotionBarData = Object.entries(emotionFreq)
        .sort((a, b) => b[1] - a[1])
        .map(([name, count]) => ({ name, count }));

    // ── Mental state frequency
    const mentalFreq: Record<string, number> = {};
    entries.forEach(e => {
        const key = e.mental_state.toLowerCase();
        mentalFreq[key] = (mentalFreq[key] || 0) + 1;
    });
    const mentalBarData = Object.entries(mentalFreq).map(([name, value]) => ({ name, value }));

    // ── Stats
    const avgCrisis = hasData
        ? (entries.reduce((a, b) => a + b.crisis_prob, 0) / entries.length * 100).toFixed(1) + '%'
        : '—';
    const avgConf = hasData
        ? (entries.reduce((a, b) => a + b.confidence, 0) / entries.length * 100).toFixed(1) + '%'
        : '—';
    const topEmotion = hasData
        ? Object.entries(emotionFreq).sort((a, b) => b[1] - a[1])[0]?.[0] || '—'
        : '—';

    return (
        <div className="flex flex-col h-full bg-[var(--bg-secondary)] rounded-2xl border border-slate-700/50 overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-700/50 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-bold text-white">Life Analytics</h2>
                {hasData && (
                    <span className="ml-auto text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-2 py-0.5">
                        LIVE
                    </span>
                )}
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-700/50 px-2">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-2.5 py-2 text-[11px] font-medium transition-all border-b-2 ${activeTab === tab.id
                                ? 'border-rose-500 text-rose-400'
                                : 'border-transparent text-slate-400 hover:text-slate-200'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-3" style={{ scrollbarWidth: 'thin', scrollbarColor: '#4f46e5 transparent' }}>
                <AnimatePresence mode="wait">

                    {/* ── TRENDS ─────────────────────────────────────── */}
                    {activeTab === 'trends' && (
                        <motion.div key="trends" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
                            <p className="text-[11px] text-slate-400 font-medium">Mood Stability (Crisis Prob)</p>
                            {hasData ? (
                                <ResponsiveContainer width="100%" height={150}>
                                    <LineChart data={trendData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748b' }} />
                                        <YAxis tick={{ fontSize: 9, fill: '#64748b' }} domain={[0, 1]} tickCount={5} />
                                        <Tooltip content={<Tip />} />
                                        <Line type="monotone" dataKey="Crisis Prob" stroke="#f87171" strokeWidth={2} dot={{ r: 3, fill: '#f87171' }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : <EmptyState label="crisis trends" />}

                            <p className="text-[11px] text-slate-400 font-medium">Emotion Confidence Over Time</p>
                            {hasData ? (
                                <ResponsiveContainer width="100%" height={130}>
                                    <LineChart data={trendData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748b' }} />
                                        <YAxis tick={{ fontSize: 9, fill: '#64748b' }} domain={[0, 1]} tickCount={5} />
                                        <Tooltip content={<Tip />} />
                                        <Line type="monotone" dataKey="Confidence" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3, fill: '#60a5fa' }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : <EmptyState label="confidence trends" />}
                        </motion.div>
                    )}

                    {/* ── INSIGHTS ───────────────────────────────────── */}
                    {activeTab === 'insights' && (
                        <motion.div key="insights" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
                            <p className="text-[11px] text-slate-400 font-medium">Most Frequent Emotions</p>
                            {hasData ? (
                                <ResponsiveContainer width="100%" height={160}>
                                    <BarChart data={emotionBarData} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                                        <XAxis type="number" tick={{ fontSize: 9, fill: '#64748b' }} />
                                        <YAxis dataKey="name" type="category" tick={{ fontSize: 9, fill: '#94a3b8' }} width={50} />
                                        <Tooltip content={<Tip />} />
                                        <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : <EmptyState label="emotion data" />}

                            <div className="grid grid-cols-2 gap-2">
                                {[
                                    { label: 'Avg Crisis', value: avgCrisis },
                                    { label: 'Avg Confidence', value: avgConf },
                                    { label: 'Top Emotion', value: topEmotion },
                                    { label: 'Session Entries', value: String(entries.length) },
                                ].map(s => (
                                    <div key={s.label} className="bg-slate-800/50 rounded-lg p-2 border border-slate-700/50">
                                        <div className="text-slate-400 text-[10px]">{s.label}</div>
                                        <div className="text-white font-bold text-sm capitalize">{s.value}</div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* ── DISTRIBUTION ───────────────────────────────── */}
                    {activeTab === 'dist' && (
                        <motion.div key="dist" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
                            <p className="text-[11px] text-slate-400 font-medium">Mental Health State Distribution</p>
                            {hasData ? (
                                <>
                                    <ResponsiveContainer width="100%" height={160}>
                                        <BarChart data={mentalBarData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                            <XAxis dataKey="name" tick={{ fontSize: 8, fill: '#64748b' }} />
                                            <YAxis tick={{ fontSize: 9, fill: '#64748b' }} />
                                            <Tooltip content={<Tip />} />
                                            <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]}>
                                                {mentalBarData.map((entry, idx) => (
                                                    <rect key={idx} fill={MENTAL_COLORS[entry.name] || '#6366f1'} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                    <div className="space-y-1">
                                        {mentalBarData.map(entry => (
                                            <div key={entry.name} className="flex items-center justify-between text-xs px-2 py-1 rounded bg-slate-800/40">
                                                <span className="flex items-center gap-2">
                                                    <span className="w-2 h-2 rounded-full" style={{ background: MENTAL_COLORS[entry.name] || '#6366f1' }} />
                                                    <span className="capitalize text-slate-300">{entry.name}</span>
                                                </span>
                                                <span className="text-slate-400">{entry.value} {entry.value === 1 ? 'entry' : 'entries'}</span>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            ) : <EmptyState label="mental health distribution" />}
                        </motion.div>
                    )}

                    {/* ── TRAINING METRICS ───────────────────────────── */}
                    {activeTab === 'training' && (
                        <motion.div key="training" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
                            <p className="text-[11px] text-slate-400 font-medium">Model Performance Radar</p>
                            <ResponsiveContainer width="100%" height={180}>
                                <RadarChart data={TRAINING_RADAR}>
                                    <PolarGrid stroke="#1e293b" />
                                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 8, fill: '#94a3b8' }} />
                                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 7, fill: '#475569' }} />
                                    <Radar name="%" dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.35} />
                                </RadarChart>
                            </ResponsiveContainer>
                            <div className="space-y-2">
                                {MODEL_INFO.map(m => (
                                    <div key={m.name} className="bg-slate-800/50 rounded-lg p-2 border border-slate-700/50">
                                        <div className="text-white text-xs font-semibold mb-1">{m.name}</div>
                                        <div className="grid grid-cols-2 gap-x-3 text-[10px] text-slate-400">
                                            <span>Algo: <span className="text-slate-300">{m.algo}</span></span>
                                            <span>Acc: <span className="text-emerald-400 font-bold">{m.accuracy}</span></span>
                                            <span>Size: <span className="text-slate-300">{m.size}</span></span>
                                            <span>Latency: <span className="text-indigo-400">{m.latency}</span></span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                </AnimatePresence>
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-slate-700/50 flex justify-between items-center">
                <span className="text-[10px] text-slate-500">
                    {hasData ? `${entries.length} real-time entr${entries.length === 1 ? 'y' : 'ies'}` : 'No entries yet'}
                </span>
                {hasData && (
                    <span className="text-[10px] text-emerald-400">● Live</span>
                )}
            </div>
        </div>
    );
}
