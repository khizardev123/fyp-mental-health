import { motion } from 'framer-motion';

interface AvatarProps {
    emotion: string;
    isThinking: boolean;
}

export default function Avatar({ emotion, isThinking }: AvatarProps) {
    // Premium Color System
    const getTheme = () => {
        switch (emotion?.toLowerCase()) {
            case 'sadness': return { primary: '#3b82f6', secondary: '#1e40af', glow: 'rgba(59, 130, 246, 0.5)' };
            case 'joy': return { primary: '#fbbf24', secondary: '#d97706', glow: 'rgba(251, 191, 36, 0.5)' };
            case 'anger': return { primary: '#ef4444', secondary: '#991b1b', glow: 'rgba(239, 68, 68, 0.5)' };
            case 'fear': return { primary: '#8b5cf6', secondary: '#5b21b6', glow: 'rgba(139, 92, 246, 0.5)' };
            case 'love': return { primary: '#f472b6', secondary: '#be185d', glow: 'rgba(244, 114, 182, 0.5)' };
            default: return { primary: '#6366f1', secondary: '#4338ca', glow: 'rgba(99, 102, 241, 0.5)' }; // Serene
        }
    };

    const theme = getTheme();

    return (
        <div className="relative w-32 h-32 flex items-center justify-center translate-z-0">
            {/* Organic Glow Layer */}
            <motion.div
                className="absolute inset-0 blur-3xl rounded-full"
                animate={{
                    scale: isThinking ? [1, 1.2, 1] : [1, 1.1, 1],
                    opacity: [0.2, 0.4, 0.2]
                }}
                transition={{ duration: 4, repeat: Infinity }}
                style={{ background: theme.primary }}
            />

            {/* Liquid Blob Container */}
            <div className="relative w-full h-full filter-liquid overflow-visible">
                <svg viewBox="0 0 200 200" className="w-full h-full">
                    <defs>
                        <filter id="liquid-filter">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
                            <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7" result="liquid" />
                        </filter>
                        <linearGradient id="blob-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor={theme.primary} />
                            <stop offset="100%" stopColor={theme.secondary} />
                        </linearGradient>
                    </defs>

                    <g filter="url(#liquid-filter)">
                        {/* Main Morphing Body */}
                        <motion.circle
                            cx="100" cy="100" r="65"
                            fill="url(#blob-gradient)"
                            animate={{
                                cx: isThinking ? [100, 105, 95, 100] : [100, 102, 98, 100],
                                cy: isThinking ? [100, 95, 105, 100] : [100, 102, 98, 100],
                                r: isThinking ? [65, 60, 68, 65] : [65, 63, 67, 65]
                            }}
                            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                        />

                        {/* Secondary Satellites for Liquid Effect */}
                        {[1, 2, 3].map((i) => (
                            <motion.circle
                                key={i}
                                cx="100" cy="100" r="30"
                                fill="url(#blob-gradient)"
                                animate={{
                                    x: isThinking ? [0, i * 15, -i * 15, 0] : [0, i * 5, -i * 5, 0],
                                    y: isThinking ? [0, -i * 15, i * 15, 0] : [0, -i * 5, i * 5, 0],
                                    scale: [1, 1.2, 0.8, 1]
                                }}
                                transition={{
                                    duration: 4 + i,
                                    repeat: Infinity,
                                    ease: "easeInOut",
                                    delay: i * 0.5
                                }}
                            />
                        ))}
                    </g>

                    {/* Minimal Face Overlay (outside filter for clarity) */}
                    <g className="drop-shadow-sm">
                        <motion.path
                            d={emotion === 'joy' ? "M70 110 Q100 135 130 110" :
                                emotion === 'sadness' ? "M75 125 Q100 110 125 125" :
                                    "M80 115 Q100 115 120 115"}
                            stroke="white" strokeWidth="4" strokeLinecap="round" fill="none"
                            animate={{ opacity: isThinking ? 0.3 : 0.8 }}
                        />
                        {/* Eyes */}
                        <motion.circle
                            cx="75" cy="90" r="3" fill="white"
                            animate={{ scaleY: isThinking ? [1, 0.1, 1] : 1 }}
                            transition={{ repeat: Infinity, duration: 3, delay: 1 }}
                        />
                        <motion.circle
                            cx="125" cy="90" r="3" fill="white"
                            animate={{ scaleY: isThinking ? [1, 0.1, 1] : 1 }}
                            transition={{ repeat: Infinity, duration: 3, delay: 1.1 }}
                        />
                    </g>
                </svg>
            </div>
        </div>
    );
}
