"use client";

import { X } from "lucide-react";
import { useState, useEffect } from "react";

export function DeprecationBanner() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user has already dismissed the banner
    const dismissed = localStorage.getItem("deprecation-banner-dismissed");
    if (!dismissed) {
      setIsVisible(true);
    }
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem("deprecation-banner-dismissed", "true");
  };

  if (!isVisible) return null;

  return (
    <div className="relative w-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-4 py-3 text-center font-medium border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-4xl mx-auto flex items-center justify-center gap-2">
        <span className="text-sm md:text-base">
          This consumer application is being deprecated to focus on our SDK and API offerings. 
          Please visit{" "}
          <a 
            href="https://docs.jeanmemory.com" 
            className="underline font-semibold hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            docs.jeanmemory.com
          </a>{" "}
          for SDK documentation and integration guides.
        </span>
        <button
          onClick={handleDismiss}
          className="absolute right-4 p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
          aria-label="Dismiss banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}