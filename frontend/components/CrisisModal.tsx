import { X, PhoneCall } from 'lucide-react';

interface CrisisModalProps {
    onClose: () => void;
}

export default function CrisisModal({ onClose }: CrisisModalProps) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-red-500/50 rounded-2xl max-w-md w-full p-6 shadow-2xl shadow-red-900/40 relative animate-fade-in">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
                >
                    <X className="w-6 h-6" />
                </button>

                <div className="text-center mb-6">
                    <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4 text-red-500">
                        <PhoneCall className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">You Are Not Alone</h2>
                    <p className="text-slate-300">
                        It looks like you might be going through a difficult time. Please reach out to someone who can help.
                    </p>
                </div>

                <div className="space-y-4">
                    <a href="tel:03174288665" className="block w-full py-4 bg-red-600 hover:bg-red-700 text-white text-center rounded-xl font-bold text-lg transition-colors">
                        Call Umang Helpline (24/7)
                    </a>
                    <a href="tel:1122" className="block w-full py-4 bg-slate-800 hover:bg-slate-700 text-white text-center rounded-xl font-bold text-lg transition-colors border border-slate-600">
                        Call Rescue 1122
                    </a>
                </div>

                <p className="text-center text-xs text-slate-500 mt-6">
                    Confidential • Free • 24/7 Support
                </p>
            </div>
        </div>
    );
}
