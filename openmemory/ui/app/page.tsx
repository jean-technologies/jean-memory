"use client";

import { useRef, useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import ParticleNetwork from "@/components/landing/ParticleNetwork";
import { useAuth } from "@/contexts/AuthContext";

export default function LandingPage() {
  const buttonRef = useRef<HTMLAnchorElement>(null);
  const router = useRouter();
  const { user, isLoading } = useAuth();

  // Redirect authenticated users to dashboard immediately
  // COMMENTED OUT: Allow authenticated users to view landing page
  // useEffect(() => {
  //   if (!isLoading && user) {
  //     console.log('Landing page: User authenticated, redirecting to dashboard');
  //     router.replace('/dashboard');
  //   }
  // }, [user, isLoading, router]);

  // Also check for Supabase OAuth callback and redirect immediately
  useEffect(() => {
    // Check if this is a Supabase OAuth callback (has access_token or code in URL)
    const urlParams = new URLSearchParams(window.location.search);
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    
    if (urlParams.get('code') || hashParams.get('access_token')) {
      console.log('Landing page: OAuth callback detected, will redirect to dashboard once auth completes');
      // Don't render the landing page content if this is an OAuth callback
      return;
    }
  }, []);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  // Don't render landing page for authenticated users (they'll be redirected)
  // COMMENTED OUT: Allow authenticated users to view landing page
  // if (user) {
  //   return (
  //     <div className="min-h-screen bg-black flex items-center justify-center">
  //       <div className="text-white">Redirecting to dashboard...</div>
  //     </div>
  //   );
  // }

  // Check if this is an OAuth callback - show loading instead of landing page
  const urlParams = new URLSearchParams(window.location.search);
  const hashParams = new URLSearchParams(window.location.hash.substring(1));
  
  if (urlParams.get('code') || hashParams.get('access_token')) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white">Completing authentication...</div>
      </div>
    );
  }

  // Show landing page for unauthenticated users
  return (
    <div className="relative min-h-screen bg-gray-50 text-gray-900 overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <ParticleNetwork id="landing-particles" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto w-full"
        >
          {/* Title */}
          <motion.h1
            className="text-6xl sm:text-7xl md:text-8xl font-semibold mb-8 text-gray-900 tracking-tight"
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Jean
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="text-xl sm:text-2xl text-gray-700 mb-2 max-w-2xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            AI that actually knows you
          </motion.p>

          <motion.p
            className="text-lg text-gray-600 mb-12 max-w-xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            Share your memory across your AI apps
          </motion.p>

          <div className="my-16 flex flex-col items-center justify-center gap-8">
            {/* CTA Buttons */}
            <motion.div
              className="flex flex-col sm:flex-row gap-4"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 20,
                delay: 0.8
              }}
            >
              <Link
                ref={buttonRef}
                href={user ? "/dashboard" : "/auth?animate=true"}
                className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 text-lg font-medium rounded-lg bg-gray-900 text-white hover:bg-gray-800 transition-all duration-200"
              >
                <span>{user ? "Go to Dashboard" : "Sign in with Jean"}</span>
              </Link>
            </motion.div>
          </div>

        </motion.div>
      </div>
    </div>
  );
}
