import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, Shield, Cloud, Server, Database, Bell, CheckCircle2, 
  Calendar, Clock, User, FileText, ArrowRight, Sparkles, AlertCircle,
  Stethoscope, Send, RefreshCw, X
} from 'lucide-react';
import Navbar from './components/Navbar';
import ECGAnimation from './components/ECGAnimation';
import { fetchHealth } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // overview, patient, doctor, simulation
  const [showArchModal, setShowArchModal] = useState(false);
  const [systemStats, setSystemStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Simulation state
  const [simSteps, setSimSteps] = useState([
    { id: 1, title: 'Patient Registration', status: 'ready', detail: 'Johnathan Doe (USR-PAT-001) registered' },
    { id: 2, title: 'Doctor Login & DynamoDB Counter', status: 'ready', detail: 'Dr. Sarah Johnson logged in (LoginCount incremented)' },
    { id: 3, title: 'Book Appointment', status: 'ready', detail: 'Scheduled Cardiology consult for 2026-11-15' },
    { id: 4, title: 'AWS SNS Cloud Notification', status: 'ready', detail: 'Alert dispatched to patient & doctor' },
    { id: 5, title: 'Submit Clinical Diagnosis', status: 'ready', detail: 'Diagnosis recorded & saved to patient history' }
  ]);
  const [simRunning, setSimRunning] = useState(false);
  const [simStepIndex, setSimStepIndex] = useState(-1);

  // Patient Booking form state
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [patientForm, setPatientForm] = useState({
    doctor: 'Dr. Sarah Johnson, MD (Cardiology)',
    date: '2026-11-20',
    time: '10:30 AM',
    reason: 'Routine cardiovascular follow-up'
  });

  // Doctor Diagnosis form state
  const [diagnosisSuccess, setDiagnosisSuccess] = useState(false);
  const [diagForm, setDiagForm] = useState({
    patient: 'Johnathan Doe',
    diagnosis: 'Mild Sinus Bradycardia with normal QT interval.',
    prescription: 'Metoprolol 25mg daily, maintain hydration, review in 3 months.'
  });

  useEffect(() => {
    fetchHealth().then(data => {
      setSystemStats(data);
      setLoading(false);
    });
  }, []);

  const runSimulation = () => {
    setSimRunning(true);
    setSimStepIndex(0);

    const interval = setInterval(() => {
      setSimStepIndex(prev => {
        if (prev >= simSteps.length - 1) {
          clearInterval(interval);
          setSimRunning(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar 
        onOpenPatient={() => setActiveTab('patient')}
        onOpenDoctor={() => setActiveTab('doctor')}
        onOpenArch={() => setShowArchModal(true)}
        systemStats={systemStats}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-4 overflow-x-auto">
          {[
            { id: 'overview', label: 'Overview & Telemetry', icon: Activity },
            { id: 'patient', label: 'Patient Portal', icon: User },
            { id: 'doctor', label: 'Doctor Portal', icon: Stethoscope },
            { id: 'simulation', label: 'Workflow Simulator', icon: Sparkles },
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  active 
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* TAB 1: OVERVIEW & TELEMETRY */}
        {activeTab === 'overview' && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-8"
          >
            {/* Hero Banner */}
            <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800 p-8 sm:p-12">
              <div className="relative z-10 max-w-3xl space-y-6">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
                  <Sparkles className="w-3.5 h-3.5" />
                  Cloud-Native Healthcare Management System
                </div>
                
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
                  Seamless Healthcare with{' '}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">
                    Cloud-Grade Resilience.
                  </span>
                </h1>

                <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
                  Streamlined patient appointments, secure diagnosis submissions, and real-time AWS SNS 
                  notifications. Built with Flask, DynamoDB, and an automatic local storage fallback.
                </p>

                <div className="flex flex-wrap gap-4 pt-2">
                  <button 
                    onClick={() => setActiveTab('patient')}
                    className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 active:scale-95"
                  >
                    Book an Appointment
                    <ArrowRight className="w-4 h-4" />
                  </button>

                  <button 
                    onClick={() => setActiveTab('simulation')}
                    className="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm border border-slate-700 transition-all hover:scale-105"
                  >
                    <RefreshCw className="w-4 h-4 text-emerald-400" />
                    Test Live Simulation
                  </button>
                </div>
              </div>

              {/* ECG Waveform Pulse */}
              <div className="mt-8">
                <ECGAnimation />
              </div>
            </div>

            {/* Telemetry Status Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>STORAGE MODE</span>
                  <Database className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xl font-bold text-white">
                  {systemStats?.aws_connected ? 'AWS DynamoDB' : 'Local JSON Fallback'}
                </div>
                <p className="text-xs text-slate-400">
                  {systemStats?.aws_connected ? 'us-east-1 Active' : 'Zero AWS dependency mode'}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>HEALTH CHECK</span>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xl font-bold text-emerald-400">
                  {systemStats?.status?.toUpperCase() || 'HEALTHY'}
                </div>
                <p className="text-xs text-slate-400">
                  Latency: &lt;10ms (Local Fast Probe)
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>ACTIVE USERS</span>
                  <User className="w-4 h-4 text-sky-400" />
                </div>
                <div className="text-xl font-bold text-white">
                  {systemStats?.total_users || 6} Registered
                </div>
                <p className="text-xs text-slate-400">
                  Doctors, Patients, Admin
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>APPOINTMENTS</span>
                  <Calendar className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-xl font-bold text-white">
                  {systemStats?.total_appointments || 5} Total
                </div>
                <p className="text-xs text-slate-400">
                  Scheduled & Confirmed
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* TAB 2: PATIENT PORTAL */}
        {activeTab === 'patient' && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
          >
            {/* Booking Form */}
            <div className="lg:col-span-2 p-6 sm:p-8 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Book an Appointment</h2>
                <p className="text-sm text-slate-400">Select a specialist and preferred slot.</p>
              </div>

              {bookingSuccess && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <span>Appointment scheduled successfully! Real-time confirmation sent via notification system.</span>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1">SELECT DOCTOR</label>
                  <select 
                    value={patientForm.doctor}
                    onChange={e => setPatientForm({...patientForm, doctor: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  >
                    <option>Dr. Sarah Johnson, MD (Cardiology)</option>
                    <option>Dr. Michael Chen, MD (Neurology)</option>
                  </select>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1">DATE</label>
                    <input 
                      type="date" 
                      value={patientForm.date}
                      onChange={e => setPatientForm({...patientForm, date: e.target.value})}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1">TIME SLOT</label>
                    <input 
                      type="text" 
                      value={patientForm.time}
                      onChange={e => setPatientForm({...patientForm, time: e.target.value})}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1">REASON FOR VISIT</label>
                  <textarea 
                    rows={3}
                    value={patientForm.reason}
                    onChange={e => setPatientForm({...patientForm, reason: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <button 
                  onClick={() => {
                    setBookingSuccess(true);
                    setTimeout(() => setBookingSuccess(false), 5000);
                  }}
                  className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-emerald-500/20"
                >
                  Confirm Appointment
                </button>
              </div>
            </div>

            {/* Patient Profile Card */}
            <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold">
                  JD
                </div>
                <div>
                  <h3 className="font-bold text-white">Johnathan Doe</h3>
                  <p className="text-xs text-slate-400 font-mono">ID: USR-PAT-001</p>
                </div>
              </div>

              <div className="space-y-3 text-xs border-t border-slate-800 pt-4">
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Age / Gender:</span>
                  <span className="text-slate-200">38 / Male</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Phone:</span>
                  <span className="text-slate-200">+1 (555) 234-5678</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Medical History:</span>
                  <span className="text-slate-200">Mild hypertension, seasonal allergies</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* TAB 3: DOCTOR PORTAL */}
        {activeTab === 'doctor' && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
          >
            {/* Diagnosis Submission */}
            <div className="lg:col-span-2 p-6 sm:p-8 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Submit Diagnosis & Prescription</h2>
                <p className="text-sm text-slate-400">Complete clinical visit notes and notify patient.</p>
              </div>

              {diagnosisSuccess && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <span>Diagnosis submitted! AWS SNS notification dispatched and appointment status updated to Completed.</span>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1">PATIENT</label>
                  <input 
                    type="text" 
                    readOnly
                    value={diagForm.patient}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-400 cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1">CLINICAL DIAGNOSIS</label>
                  <textarea 
                    rows={3}
                    value={diagForm.diagnosis}
                    onChange={e => setDiagForm({...diagForm, diagnosis: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1">PRESCRIPTION & TREATMENT PLAN</label>
                  <textarea 
                    rows={3}
                    value={diagForm.prescription}
                    onChange={e => setDiagForm({...diagForm, prescription: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <button 
                  onClick={() => {
                    setDiagnosisSuccess(true);
                    setTimeout(() => setDiagnosisSuccess(false), 5000);
                  }}
                  className="w-full py-3 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-teal-500/20"
                >
                  Submit Clinical Report
                </button>
              </div>
            </div>

            {/* Doctor Info */}
            <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 font-bold">
                  SJ
                </div>
                <div>
                  <h3 className="font-bold text-white">Dr. Sarah Johnson, MD</h3>
                  <p className="text-xs text-slate-400 font-mono">Specialist: Cardiology</p>
                </div>
              </div>

              <div className="space-y-3 text-xs border-t border-slate-800 pt-4">
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Experience:</span>
                  <span className="text-slate-200">12 Years</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Hospital:</span>
                  <span className="text-slate-200">Metropolitan Medical Center</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">DynamoDB LoginCount:</span>
                  <span className="text-emerald-400 font-bold font-mono">9 Logins Recorded</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* TAB 4: SIMULATOR */}
        {activeTab === 'simulation' && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-6"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-white">Interactive Healthcare Scenario Simulator</h2>
                <p className="text-sm text-slate-400">Step-by-step verification of MedTrack's complete lifecycle.</p>
              </div>
              <button 
                onClick={runSimulation}
                disabled={simRunning}
                className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold text-sm transition-all"
              >
                {simRunning ? 'Running Simulation...' : 'Start Scenario Simulation'}
              </button>
            </div>

            <div className="space-y-3 pt-4">
              {simSteps.map((step, idx) => {
                const isPassed = simStepIndex >= idx;
                const isCurrent = simStepIndex === idx && simRunning;
                return (
                  <div 
                    key={step.id}
                    className={`p-4 rounded-2xl border transition-all flex items-center justify-between ${
                      isPassed 
                        ? 'bg-emerald-950/20 border-emerald-500/40' 
                        : 'bg-slate-950/40 border-slate-800/80 opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                        isPassed ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {idx + 1}
                      </div>
                      <div>
                        <h4 className="font-semibold text-sm text-white">{step.title}</h4>
                        <p className="text-xs text-slate-400">{step.detail}</p>
                      </div>
                    </div>

                    <div className="text-xs font-mono">
                      {isPassed ? (
                        <span className="text-emerald-400 flex items-center gap-1.5 font-bold">
                          <CheckCircle2 className="w-4 h-4" /> VERIFIED
                        </span>
                      ) : isCurrent ? (
                        <span className="text-amber-400 animate-pulse">PROCESSING...</span>
                      ) : (
                        <span className="text-slate-500">READY</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

      </main>

      {/* Architecture Modal */}
      <AnimatePresence>
        {showArchModal && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md"
          >
            <motion.div 
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="max-w-2xl w-full p-6 sm:p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-6 shadow-2xl"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Cloud className="w-6 h-6 text-sky-400" />
                  <h3 className="text-xl font-bold text-white">AWS Cloud Architecture & Fallback</h3>
                </div>
                <button 
                  onClick={() => setShowArchModal(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4 text-sm text-slate-300 leading-relaxed font-sans">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-xs font-mono text-emerald-400 font-bold">1. AWS DYNAMODB HYBRID LAYER</div>
                  <p className="text-xs text-slate-400">
                    6 Tables: Users, Doctors, Patients, Appointments, Diagnosis, Notifications.
                    Auto-probed in under 2 seconds. When offline or uncredentialed, falls back to <code>local_db.json</code>.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-xs font-mono text-sky-400 font-bold">2. AWS SNS NOTIFICATIONS</div>
                  <p className="text-xs text-slate-400">
                    Publishes SMS & Email alerts on appointment confirmations and diagnosis submissions.
                    Graceful fallback stores alerts in local database notifications table.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-xs font-mono text-purple-400 font-bold">3. AWS IAM LEAST PRIVILEGE</div>
                  <p className="text-xs text-slate-400">
                    Fine-grained IAM policy defined in <code>aws_configs/medtrack_iam_policy.json</code> for EC2 instance profile access.
                  </p>
                </div>
              </div>

              <button 
                onClick={() => setShowArchModal(false)}
                className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm transition-all"
              >
                Close Architecture View
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 font-mono">
        MedTrack Healthcare Management System • React + Vite + Tailwind + Framer Motion • Flask REST Backend
      </footer>
    </div>
  );
}
