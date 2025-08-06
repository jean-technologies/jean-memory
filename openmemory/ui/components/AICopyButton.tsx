"use client";

import React, { useState } from 'react';
import { Bot, Copy, Check, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

interface AICopyButtonProps {
  content: string;
  title?: string;
  className?: string;
}

export const AICopyButton: React.FC<AICopyButtonProps> = ({ 
  content, 
  title = "AI Quick Deploy",
  className = ""
}) => {
  const [copied, setCopied] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className={`relative ${className}`}>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="inline-block"
      >
        <Button
          onClick={handleCopy}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          className={`
            group relative overflow-hidden
            ${copied 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
            }
            text-white font-medium px-6 py-3 rounded-lg
            transition-all duration-300 transform hover:scale-105
            shadow-lg hover:shadow-xl
          `}
        >
          <span className="relative z-10 flex items-center gap-2">
            {copied ? (
              <>
                <Check className="w-5 h-5" />
                <span>Copied! Paste into Claude</span>
              </>
            ) : (
              <>
                <Bot className="w-5 h-5" />
                <span>{title}</span>
                <Sparkles className="w-4 h-4 opacity-70" />
              </>
            )}
          </span>
          
          {/* Animated background gradient */}
          <motion.div
            className="absolute inset-0 opacity-30"
            animate={{
              background: [
                'linear-gradient(45deg, #9333ea, #3b82f6)',
                'linear-gradient(45deg, #3b82f6, #9333ea)',
                'linear-gradient(45deg, #9333ea, #3b82f6)',
              ],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        </Button>

        {/* Tooltip */}
        <AnimatePresence>
          {showTooltip && !copied && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50"
            >
              <div className="bg-slate-800 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-xl">
                <div className="font-semibold mb-1">AI-Optimized Documentation</div>
                <div className="text-slate-300">Copy complete implementation guide for AI agents</div>
                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-slate-800"></div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Success message */}
      <AnimatePresence>
        {copied && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="absolute top-0 left-full ml-4 flex items-center"
          >
            <div className="bg-green-500/20 border border-green-500/30 text-green-300 px-3 py-2 rounded-lg text-sm whitespace-nowrap">
              Ready to paste into any AI chat!
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AICopyButton;