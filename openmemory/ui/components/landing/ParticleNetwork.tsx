"use client";

import { useCallback, useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadFull } from "tsparticles";
import { useTheme } from "next-themes";

interface ParticleNetworkProps {
  id: string;
  className?: string;
  interactive?: boolean;
  particleCount?: number;
}

export default function ParticleNetwork({ 
  id,
  className, 
  interactive = true, 
  particleCount = 200 
}: ParticleNetworkProps) {
  const [init, setInit] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const { theme } = useTheme();

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadFull(engine);
    }).then(() => {
      setInit(true);
    });
  }, []);

  const particlesLoaded = useCallback(async (container: any) => {
    // Optional callback
  }, []);

  const particleColors = theme === 'light' 
    ? ["#718096", "#a0aec0", "#cbd5e0"] // Steel gray palette for light mode
    : ["#9ca3af", "#6b7280", "#4b5563"]; // Original palette for dark mode
  
  const linkColor = theme === 'light' ? "#a0aec0" : "#6b7280";

  // Desktop: Full interactive experience
  // Mobile: Simplified but visible
  const options = {
    fullScreen: {
      enable: false,
      zIndex: 0,
    },
    background: {
      color: {
        value: "transparent",
      },
    },
    fpsLimit: 120,
    interactivity: {
      events: {
        onClick: {
          enable: interactive && !isMobile, // Desktop only: click to add particles
          mode: "push",
        },
        onHover: {
          enable: interactive && !isMobile, // Desktop only: hover connections
          mode: "grab",
        },
      },
      modes: {
        push: {
          quantity: 2,
        },
        grab: {
          distance: 120,
          links: {
            opacity: 0.3,
          },
        },
      },
    },
    particles: {
      color: {
        value: isMobile 
          ? particleColors[1] // a mid-range color for mobile
          : particleColors,
      },
              links: {
          color: linkColor,
          distance: 100,
          enable: true,
          opacity: isMobile ? 0.4 : 0.2, // Much more subtle
          width: 1,
        },
      move: {
        direction: "none",
        enable: true,
        outModes: {
          default: "bounce",
        },
        random: true,
        speed: isMobile ? 0.5 : 0.6, // Much slower and more subtle
        straight: false,
      },
      number: {
        value: isMobile ? 30 : 80, // Significantly fewer particles
      },
              opacity: {
          value: isMobile ? 0.5 : 0.3, // Much more subtle
        },
      shape: {
        type: "circle",
      },
      size: {
        value: { min: 1, max: isMobile ? 3 : 3 }, // Consistent size
      },
    },
    detectRetina: true,
  };

  if (!init) {
    return null;
  }

  return (
    <Particles
      id={id}
      className={className}
      particlesLoaded={particlesLoaded}
      options={options as any}
    />
  );
} 