"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import ParticleNetwork from "@/components/landing/ParticleNetwork";
import AnimatedCodeBlock from "@/components/landing/AnimatedCodeBlock";

export default function LandingPage() {
  const { user } = useAuth();
  const [showFor, setShowFor] = useState<"user" | "developer">("user");

  return (
    <div className="relative bg-gray-50 text-gray-900 min-h-screen overflow-x-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="landing-particles" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto w-full"
        >
          <motion.h1
            className="text-6xl sm:text-7xl md:text-8xl font-semibold mb-8 text-gray-900 tracking-tight"
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Jean
          </motion.h1>

          <motion.p
            className="text-xl sm:text-2xl text-gray-700 mb-12 max-w-2xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            AI that actually knows you.
            <br />
            Share your memory across your AI apps.
          </motion.p>
        </motion.div>

        {/* Path Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="flex justify-center bg-gray-200/70 p-1 rounded-lg mb-12"
        >
          <button
            onClick={() => setShowFor("user")}
            className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
              showFor === "user" ? "bg-white shadow" : "text-gray-600"
            }`}
          >
            For Users
          </button>
          <button
            onClick={() => setShowFor("developer")}
            className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
              showFor === "developer" ? "bg-white shadow" : "text-gray-600"
            }`}
          >
            For Developers
          </button>
        </motion.div>

        {/* Content based on toggle */}
        <div className="w-full max-w-4xl">
          {showFor === "user" ? (
            <motion.div
              key="user-path"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center"
            >
              <p className="text-gray-600 mb-6">
                Connect your memory once. Use it everywhere.
              </p>
              <Link
                href={user ? "/dashboard" : "/auth?animate=true"}
                className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 text-lg font-medium rounded-lg bg-gray-900 text-white hover:bg-gray-800 transition-all duration-200"
              >
                <span>{user ? "Go to Dashboard" : "Sign in with Jean"}</span>
              </Link>
            </motion.div>
          ) : (
            <motion.div
              key="developer-path"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center"
            >
              <p className="text-gray-600 mb-6 text-center">
                Add personalized AI to your app in 5 lines of code.
              </p>
              <AnimatedCodeBlock />
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
