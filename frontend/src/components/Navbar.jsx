import React from 'react';
import { Activity, Shield, Cloud, Server, Database, Bell } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Navbar({ onOpenPatient, onOpenDoctor, onOpenArch, systemStats }) {
  const isAws = systemStats?.aws_connected;

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo */}
        <motion.div 
          className="flex items-center gap-3 cursor-pointer"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-slate-950 shadow-lg shadow-emerald-500/20">
            <Activity className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white">MedTrack</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                v2.0 AWS
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Healthcare Management System</p>
          </div>
        </motion.div>

        {/* Status Badge */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono">
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isAws ? 'bg-amber-400' : 'bg-emerald-400'}`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${isAws ? 'bg-amber-500' : 'bg-emerald-500'}`}></span>
          </span>
          <span className="text-slate-300">
            {isAws ? 'AWS DynamoDB Mode' : 'Local Storage (Auto-Fallback Active)'}
          </span>
        </div>

        {/* Action Controls */}
        <motion.div 
          className="flex items-center gap-3"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <button 
            onClick={onOpenArch}
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-800 border border-slate-800 transition-colors"
          >
            <Cloud className="w-4 h-4 text-sky-400" />
            AWS Architecture
          </button>

          <button 
            onClick={onOpenPatient}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-900 bg-emerald-400 hover:bg-emerald-300 shadow-sm shadow-emerald-500/20 transition-all hover:scale-105 active:scale-95"
          >
            Patient Portal
          </button>

          <button 
            onClick={onOpenDoctor}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all hover:scale-105 active:scale-95"
          >
            Doctor Portal
          </button>
        </motion.div>
      </div>
    </header>
  );
}
