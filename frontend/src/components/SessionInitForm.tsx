// frontend/src/components/SessionInitForm.tsx
// Step 15 — Session initiation form (case ID, specialist ID, session token)

import React, { useState } from 'react';
import { LogIn, Shield, Key, User, Hash } from 'lucide-react';

interface SessionInitFormProps {
  onSubmit: (caseId: string, specialistId: string, sessionToken: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const SessionInitForm: React.FC<SessionInitFormProps> = ({ onSubmit, isLoading, error }) => {
  const [caseId, setCaseId] = useState('');
  const [specialistId, setSpecialistId] = useState('');
  const [sessionToken, setSessionToken] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseId.trim() || !specialistId.trim() || !sessionToken.trim()) return;
    await onSubmit(caseId.trim(), specialistId.trim(), sessionToken.trim());
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a0f1e]">
      {/* Background gradient */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-[#3b82f6]/5 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-[#10b981]/5 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#1d3f7a]/40 border border-[#3b82f6]/30 mb-4 shadow-[0_0_30px_rgba(59,130,246,0.2)]">
            <Shield size={32} className="text-[#3b82f6]" />
          </div>
          <h1 className="text-2xl font-bold text-[#e2e8f8] tracking-tight">Bridge-PA</h1>
          <p className="text-sm text-[#4a5f82] mt-1">Prior Authorization Orchestration System</p>
          <div className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-[#1e2d4a] bg-[#0f1629] px-3 py-1 text-xs text-[#8899bb]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#10b981] animate-pulse" />
            HIPAA-Compliant · Semi-Autonomous
          </div>
        </div>

        {/* Form Card */}
        <div className="card shadow-[0_0_40px_rgba(0,0,0,0.4)]">
          <h2 className="text-base font-semibold text-[#e2e8f8] mb-1">Initiate Case Session</h2>
          <p className="text-xs text-[#4a5f82] mb-5">
            Concurrent Review — Prior Authorization processing only. Enter your credentials to begin.
          </p>

          {error && (
            <div className="mb-4 rounded-lg border border-[#ef4444]/30 bg-[#3d0f0f]/30 p-3 text-sm text-[#ef4444]" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Case ID */}
            <div>
              <label htmlFor="case-id" className="block text-xs font-medium text-[#8899bb] mb-1.5">
                Case ID <span className="text-[#ef4444]">*</span>
              </label>
              <div className="relative">
                <Hash size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a5f82]" />
                <input
                  id="case-id"
                  type="text"
                  className="w-full rounded-lg border border-[#1e2d4a] bg-[#0a0f1e] pl-9 pr-3 py-2.5 text-sm text-[#e2e8f8] placeholder:text-[#4a5f82] focus:outline-none focus:border-[#3b82f6] transition-colors"
                  placeholder="e.g. PA-2026-00123"
                  value={caseId}
                  onChange={e => setCaseId(e.target.value)}
                  required
                  autoFocus
                />
              </div>
            </div>

            {/* Specialist ID */}
            <div>
              <label htmlFor="specialist-id" className="block text-xs font-medium text-[#8899bb] mb-1.5">
                UM Specialist ID <span className="text-[#ef4444]">*</span>
              </label>
              <div className="relative">
                <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a5f82]" />
                <input
                  id="specialist-id"
                  type="text"
                  className="w-full rounded-lg border border-[#1e2d4a] bg-[#0a0f1e] pl-9 pr-3 py-2.5 text-sm text-[#e2e8f8] placeholder:text-[#4a5f82] focus:outline-none focus:border-[#3b82f6] transition-colors"
                  placeholder="e.g. SP-001"
                  value={specialistId}
                  onChange={e => setSpecialistId(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Session Token */}
            <div>
              <label htmlFor="session-token" className="block text-xs font-medium text-[#8899bb] mb-1.5">
                Session Token <span className="text-[#ef4444]">*</span>
              </label>
              <div className="relative">
                <Key size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a5f82]" />
                <input
                  id="session-token"
                  type="password"
                  className="w-full rounded-lg border border-[#1e2d4a] bg-[#0a0f1e] pl-9 pr-3 py-2.5 text-sm text-[#e2e8f8] placeholder:text-[#4a5f82] focus:outline-none focus:border-[#3b82f6] transition-colors"
                  placeholder="Session token (never stored)"
                  value={sessionToken}
                  onChange={e => setSessionToken(e.target.value)}
                  required
                />
              </div>
              <p className="text-[11px] text-[#4a5f82] mt-1">Session token is verified once and never displayed or stored.</p>
            </div>

            <button
              id="btn-initiate-session"
              type="submit"
              className="btn-primary w-full justify-center py-2.5 text-base font-semibold mt-2"
              disabled={isLoading || !caseId.trim() || !specialistId.trim() || !sessionToken.trim()}
            >
              {isLoading ? (
                <>
                  <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  Initiating session...
                </>
              ) : (
                <>
                  <LogIn size={16} />
                  Initiate Case Session
                </>
              )}
            </button>
          </form>

          <div className="mt-4 border-t border-[#1e2d4a] pt-4 text-xs text-[#4a5f82]">
            <p className="flex items-center gap-1.5">
              <Shield size={10} />
              Concurrent Review cases only. Out-of-scope case types will be rejected.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
