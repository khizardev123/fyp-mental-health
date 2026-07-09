"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import SafetyPanel from '@/components/SafetyPanel';
import JournalArea from '@/components/JournalArea';
import AnalyticsPanel from '@/components/AnalyticsPanel';

interface AnalyticsEntry {
    label: string;
    crisis_prob: number;
    emotion: string;
    confidence: number;
    mental_state: string;
    severity: number;
    tags: string[];
    text_emotion?: string;
    face_emotion?: string | null;
    final_avatar_emotion?: string;
    is_stress?: boolean;
}

export default function Dashboard() {
    const router = useRouter();
    const [authChecked, setAuthChecked] = useState(false);
    const [analyticsEntries, setAnalyticsEntries] = useState<AnalyticsEntry[]>([]);
    const [totalEntries, setTotalEntries] = useState(0);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.replace('/');
            return;
        }
        setAuthChecked(true);
    }, [router]);

    const handleNewEntry = (entry: {
        emotion: string; confidence: number; crisis_prob: number;
        mental_state: string; severity: number; tags: string[];
        text_emotion?: string;
        face_emotion?: string | null;
        final_avatar_emotion?: string;
        is_stress?: boolean;
    }) => {
        setTotalEntries(prev => {
            const next = prev + 1;
            setAnalyticsEntries(prev => [...prev, {
                label: `L${next}`,
                ...entry,
            }]);
            return next;
        });
    };

    if (!authChecked) {
        return null;
    }

    return (
        <main className="min-h-screen bg-[var(--bg-primary)] p-4 md:p-6 lg:p-8 h-screen overflow-hidden flex flex-col">
            <header className="flex justify-between items-center mb-6 px-2">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
                    SereneMind
                </h1>
                <div className="flex items-center gap-4">
                    <div className="text-sm text-slate-400">Welcome, Friend</div>
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600" />
                </div>
            </header>

            <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
                {/* Left: Safety & Resources */}
                <div className="col-span-12 lg:col-span-3 h-full">
                    <SafetyPanel />
                </div>

                {/* Center: Journal & Avatar Chat */}
                <div className="col-span-12 lg:col-span-6 h-full flex flex-col">
                    <JournalArea onNewEntry={handleNewEntry} />
                </div>

                {/* Right: Analytics Panel */}
                <div className="col-span-12 lg:col-span-3 h-full">
                    <AnalyticsPanel entries={analyticsEntries} totalEntries={totalEntries} />
                </div>
            </div>
        </main>
    );
}
