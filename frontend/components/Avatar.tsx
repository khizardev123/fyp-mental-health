import { motion } from 'framer-motion';

interface AvatarProps {
    emotion: string;
    isThinking: boolean;
}

export default function Avatar({ emotion, isThinking }: AvatarProps) {
    // Determine colors based on emotion
    const getColors = () => {
        switch (emotion?.toLowerCase()) {
            case 'sadness': return ['#3b82f6', '#1d4ed8'];
            case 'joy': return ['#facc15', '#f59e0b'];
            case 'anger': return ['#ef4444', '#b91c1c'];
            case 'fear': return ['#8b5cf6', '#6d28d9'];
            case 'love': return ['#ec4899', '#be185d'];
            default: return ['#6366f1', '#4f46e5']; // Neutral/Serene
        }
    };

    const [primary, secondary] = getColors();

    return (
        <div className="relative w-32 h-32 flex items-center justify-center">
            {/* Glow Effect */}
            <motion.div
                className="absolute inset-0 rounded-full blur-xl opacity-40"
                animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                style={{ background: primary }}
            />

            {/* Core Avatar SVG */}
            <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-lg">
                <defs>
                    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style={{ stopColor: primary, stopOpacity: 1 }} />
                        <stop offset="100%" style={{ stopColor: secondary, stopOpacity: 1 }} />
                    </linearGradient>
                </defs>

                <motion.circle
                    cx="50" cy="50" r="45"
                    fill="url(#grad1)"
                    animate={{
                        scale: isThinking ? [1, 0.95, 1] : 1,
                        rotate: isThinking ? [0, 5, -5, 0] : 0
                    }}
                    transition={{
                        duration: isThinking ? 0.5 : 2,
                        repeat: Infinity
                    }}
                />

                {/* Simple Face Expression (Abstract) */}
                <motion.path
                    d="M30 40 Q50 45 70 40" // Eyes line
                    stroke="white" strokeWidth="3" strokeLinecap="round" fill="none"
                    animate={{ d: emotion === 'joy' ? "M30 45 Q50 35 70 45" : "M30 40 Q50 45 70 40" }}
                />

                <motion.path
                    d="M40 65 Q50 75 60 65" // Smile/Mouth
                    stroke="white" strokeWidth="3" strokeLinecap="round" fill="none"
                    animate={{
                        d: emotion === 'joy' ? "M35 60 Q50 80 65 60" :
                            emotion === 'sadness' ? "M35 70 Q50 60 65 70" :
                                "M40 65 Q50 65 60 65"
                    }}
                />
            </svg>
        </div>
    );
}
