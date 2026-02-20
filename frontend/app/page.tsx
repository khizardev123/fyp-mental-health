"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function Home() {
    const router = useRouter();

    useEffect(() => {
        // Check auth, redirect to dashboard or login
        const token = localStorage.getItem("token");
        if (token) {
            // In a real app we'd verify the token validity here
            router.push("/dashboard");
        } else {
            // For prototype, we can also redirect to dashboard using a demo login if we want, 
            // but let's stick to a landing page that offers "Login" or "Get Started".
        }
    }, [router]);

    const handleDemoLogin = () => {
        // Quick demo access
        localStorage.setItem("token", "demo-token");
        localStorage.setItem("user", JSON.stringify({ id: "demo-user", name: "Guest" }));
        router.push("/dashboard");
    };

    return (
        <main className="min-h-screen flex flex-col items-center justify-center p-8 relative overflow-hidden">
            {/* Background Gradient Blob */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
                <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
                <div className="absolute bottom-[-20%] left-[20%] w-[500px] h-[500px] bg-pink-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
            </div>

            <div className="z-10 text-center max-w-2xl">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                >
                    <h1 className="text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
                        SereneMind
                    </h1>
                    <p className="text-xl text-gray-400 mb-12 leading-relaxed">
                        Your empathetic AI companion for mental well-being. <br />
                        Journal safely, gain insights, and find your balance.
                    </p>
                </motion.div>

                <motion.div
                    className="flex gap-4 justify-center"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4, duration: 0.8 }}
                >
                    <button
                        onClick={handleDemoLogin}
                        className="px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-semibold text-lg transition-all shadow-lg hover:shadow-indigo-500/30"
                    >
                        Enter Serenity
                    </button>
                    <button className="px-8 py-4 bg-transparent border border-gray-600 hover:border-gray-400 text-gray-300 rounded-full font-semibold text-lg transition-all">
                        Learn More
                    </button>
                </motion.div>
            </div>

            <footer className="absolute bottom-8 text-gray-600 text-sm">
                © 2024 SereneMind AI • Privacy First • End-to-End Encrypted
            </footer>
        </main>
    );
}
