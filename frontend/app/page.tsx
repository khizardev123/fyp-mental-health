"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { auth } from "@/lib/api";

const DEMO_EMAIL = "demo@example.com";
const DEMO_PASSWORD = "demo12345";

export default function Home() {
    const router = useRouter();
    const [authError, setAuthError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token) {
            router.push("/dashboard");
        }
    }, [router]);

    const handleDemoLogin = async () => {
        setAuthError(null);
        setIsLoading(true);
        try {
            let res;
            try {
                res = await auth.login({ email: DEMO_EMAIL, password: DEMO_PASSWORD });
            } catch {
                res = await auth.register({
                    name: "Guest",
                    email: DEMO_EMAIL,
                    password: DEMO_PASSWORD,
                });
            }
            const { token, user } = res.data;
            localStorage.setItem("token", token);
            localStorage.setItem("user", JSON.stringify(user));
            router.push("/dashboard");
        } catch {
            setAuthError("Sign-in failed. Please try again.");
        } finally {
            setIsLoading(false);
        }
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
                        disabled={isLoading}
                        className="px-8 py-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-full font-semibold text-lg transition-all shadow-lg hover:shadow-indigo-500/30"
                    >
                        {isLoading ? "Signing in..." : "Enter Serenity"}
                    </button>
                    {authError && (
                        <p className="mt-4 text-sm text-red-400" role="alert">
                            {authError}
                        </p>
                    )}
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
