import React from 'react';
import { motion } from 'framer-motion';

export default function ECGAnimation() {
  return (
    <div className="relative w-full h-24 overflow-hidden rounded-xl bg-slate-900/60 border border-emerald-500/20 flex items-center px-4">
      {/* Background Grid */}
      <div 
        className="absolute inset-0 opacity-10" 
        style={{
          backgroundImage: 'linear-gradient(to right, #10b981 1px, transparent 1px), linear-gradient(to bottom, #10b981 1px, transparent 1px)',
          backgroundSize: '16px 16px'
        }}
      />
      
      {/* Animated Glowing ECG Pulse Line */}
      <svg className="w-full h-16 relative z-10" viewBox="0 0 800 60" fill="none">
        <defs>
          <linearGradient id="ecgGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.1" />
            <stop offset="70%" stopColor="#10b981" stopOpacity="1" />
            <stop offset="100%" stopColor="#34d399" stopOpacity="1" />
          </linearGradient>
        </defs>
        
        <motion.path
          d="M 0 30 L 150 30 L 170 30 L 180 10 L 190 50 L 205 5 L 220 40 L 230 30 L 380 30 L 400 30 L 410 10 L 420 50 L 435 5 L 450 40 L 460 30 L 610 30 L 630 30 L 640 10 L 650 50 L 665 5 L 680 40 L 690 30 L 800 30"
          stroke="url(#ecgGrad)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0, opacity: 0.2 }}
          animate={{ 
            pathLength: [0, 1],
            opacity: [0.3, 1, 0.3],
            x: [0, -100]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear"
          }}
        />
      </svg>

      <div className="absolute right-4 top-2 flex items-center gap-2 text-xs font-mono text-emerald-400">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        LIVE TELEMETRY: 72 BPM
      </div>
    </div>
  );
}
