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
    <div className="relative w-full bg-amber-500 text-black px-4 py-3 text-center font-medium">
      <div className="max-w-4xl mx-auto flex items-center justify-center gap-2">
        <span className="text-sm md:text-base">
          ⚠️ This consumer application is being deprecated to focus on our SDK and API offerings. 
          Please visit{" "}
          <a 
            href="https://docs.jeanmemory.com" 
            className="underline font-bold hover:text-amber-900 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            docs.jeanmemory.com
          </a>{" "}
          for SDK documentation and integration guides.
        </span>
        <button
          onClick={handleDismiss}
          className="absolute right-4 p-1 hover:bg-amber-600 rounded transition-colors"
          aria-label="Dismiss banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}