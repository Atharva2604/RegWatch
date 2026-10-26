import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Lock,
  Mail,
  CheckCircle2,
  Cpu,
  Layers,
} from 'lucide-react';
import { supabase } from '../lib/supabase';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDemoLogin = () => {
    localStorage.setItem('regwatch_user', JSON.stringify({ role: 'officer', name: 'Atharva S.' }));
    navigate('/');
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.message || 'Login failed. Try the 1-Click Demo Login.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 rounded-3xl overflow-hidden glass-panel border-slate-800 shadow-2xl">
        {/* Left: Branding & Feature Highlights */}
        <div className="p-8 lg:p-10 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/40 flex flex-col justify-between border-b md:border-b-0 md:border-r border-slate-800">
          <div>
            <div className="flex items-center gap-2.5 mb-8">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <ShieldCheck className="w-6 h-6 text-slate-950" />
              </div>
              <div>
                <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  RegWatch
                </span>
                <p className="text-[10px] font-semibold text-cyan-400">
                  Regulatory Compliance Intelligence
                </p>
              </div>
            </div>

            <h2 className="text-xl font-bold text-white mb-3 leading-snug">
              Continuous Regulatory Parity for SEBI Intermediaries
            </h2>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Empowering financial brokerages, depository participants, and wealth funds with automated baseline audits, pre-change impact simulators, and 100% explainable AI traces.
            </p>

            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>3,030 SEBI regulations embedded in pgvector</span>
              </div>
              <div className="flex items-center gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>Automated Onboarding Baseline Audit</span>
              </div>
              <div className="flex items-center gap-2.5 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>Groq LPU high-speed inference & reasoning</span>
              </div>
            </div>
          </div>

          <div className="pt-8 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Client: FinCorp Securities</span>
            <span className="text-emerald-400 font-medium">SEBI Reg #INZ00018932</span>
          </div>
        </div>

        {/* Right: Login Form */}
        <div className="p-8 lg:p-10 flex flex-col justify-center bg-slate-950/70">
          <div className="mb-6">
            <h3 className="text-lg font-bold text-white mb-1">Sign In to Command Portal</h3>
            <p className="text-xs text-slate-400">Access compliance alerts and parity matrices.</p>
          </div>

          {/* 1-Click Demo Login CTA */}
          <div className="mb-6">
            <button
              onClick={handleDemoLogin}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-cyan-500/20 hover:scale-[1.01]"
            >
              <Sparkles className="w-4 h-4" />
              <span>1-Click Demo Access (FinCorp Officer)</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>
            <p className="text-center text-[10px] text-slate-400 mt-1.5">
              Instant access without credentials.
            </p>
          </div>

          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-slate-800"></div>
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Or email login</span>
            <div className="flex-1 h-px bg-slate-800"></div>
          </div>

          {errorMsg && (
            <div className="p-3 mb-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 text-xs">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleEmailLogin} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Corporate Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@fincorp.example.com"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-colors"
            >
              {loading ? 'Authenticating...' : 'Sign In with Supabase Auth'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
