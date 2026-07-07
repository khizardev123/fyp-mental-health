import { Shield, Phone, HeartHandshake } from 'lucide-react';
import { useState } from 'react';
import CrisisModal from './CrisisModal';

export default function SafetyPanel() {
    const [showModal, setShowModal] = useState(false);

    const helplines = [
        { name: "Umang Pakistan", number: "0317-4288665", desc: "24/7 Mental Health Helpline" },
        { name: "Rozan Helpline", number: "0800-22444", desc: "Counseling for women & children" },
        { name: "Talk2Me", number: "0333-333-2222", desc: "Free mental health support" },
    ];

    return (
        <div className="card h-full flex flex-col gap-6">
            <div className="flex items-center gap-3 text-indigo-400">
                <Shield className="w-6 h-6" />
                <h2 className="text-xl font-bold">Safe Space</h2>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">Privacy Status</h3>
                <div className="flex items-center gap-2 text-green-400 text-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    AES-256-GCM Encrypted
                </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">Emergency Resources</h3>
                <div className="space-y-3">
                    {helplines.map((line, idx) => (
                        <div key={idx} className="bg-slate-800/30 p-3 rounded-lg border border-slate-700 hover:border-indigo-500/30 transition-colors">
                            <div className="font-medium text-indigo-300">{line.name}</div>
                            <div className="text-lg font-bold text-white tracking-wide">{line.number}</div>
                            <div className="text-xs text-slate-400">{line.desc}</div>
                        </div>
                    ))}
                </div>
            </div>

            <button
                onClick={() => setShowModal(true)}
                className="w-full py-3 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg font-semibold hover:bg-red-500 hover:text-white transition-all flex items-center justify-center gap-2"
            >
                <Phone className="w-4 h-4" />
                Get Immediate Help
            </button>

            {showModal && <CrisisModal onClose={() => setShowModal(false)} />}
        </div>
    );
}
