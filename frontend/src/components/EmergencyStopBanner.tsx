// frontend/src/components/EmergencyStopBanner.tsx
// Step 15 — Full-width persistent Emergency Stop banner
// Spec: Cannot be dismissed by specialist. Names trigger condition explicitly.

import React from 'react';
import { OctagonX, Clock } from 'lucide-react';

interface EmergencyStopBannerProps {
  reason: string;
  scope: string;
  timestamp: string;
  caseId: string;
}

export const EmergencyStopBanner: React.FC<EmergencyStopBannerProps> = ({
  reason,
  scope,
  timestamp,
  caseId,
}) => {
  return (
    <div
      className="w-full border-y-2 border-[#ef4444] bg-[#3d0f0f]/60 backdrop-blur-sm px-6 py-4"
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="mx-auto max-w-screen-2xl">
        <div className="flex items-start gap-4">
          <OctagonX size={24} className="text-[#ef4444] shrink-0 mt-0.5 animate-pulse" />
          <div className="flex-1">
            <h2 className="text-base font-bold text-[#ef4444] tracking-wide">
              EMERGENCY STOP — All workflow processing halted
            </h2>
            <div className="mt-1 grid gap-1 text-sm text-[#cc8888]">
              <p><span className="font-semibold text-[#ef4444]">Trigger condition:</span> {reason}</p>
              <p><span className="font-semibold text-[#ef4444]">Scope:</span> {scope === 'system' ? 'System-wide (all active cases)' : `Case ${caseId}`}</p>
              <p className="flex items-center gap-1.5 text-xs text-[#4a5f82] mt-1">
                <Clock size={11} />
                {new Date(timestamp).toLocaleString()}
              </p>
            </div>
            <div className="mt-3 rounded-lg border border-[#ef4444]/20 bg-[#0a0f1e] p-3">
              <p className="text-sm font-semibold text-[#e2e8f8]">
                Awaiting UM Department Manager restart authorization.
              </p>
              <p className="text-xs text-[#4a5f82] mt-1">
                No further action is available to the specialist until restart is authorized.
                Do not close this window.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


// frontend/src/components/SLAAlertBanner.tsx
// Step 15 — SLA threshold alert banner (48h/60h/66h)

export const SLAAlertBanner: React.FC<{ level: string; caseId: string; elapsedHours: number }> = ({
  level,
  caseId,
  elapsedHours,
}) => {
  const config = {
    standard: {
      bg: 'bg-[#3d2a00]/60 border-[#f59e0b]',
      text: 'text-[#f59e0b]',
      label: 'SLA Alert — Standard',
      detail: `Case ${caseId} has been active for ${Math.floor(elapsedHours)}h. CMS 72-hour deadline: ${Math.floor(72 - elapsedHours)}h remaining.`,
    },
    critical: {
      bg: 'bg-[#3d1a00]/60 border-[#f97316]',
      text: 'text-[#f97316]',
      label: 'SLA Alert — Critical',
      detail: `Case ${caseId} has been active for ${Math.floor(elapsedHours)}h. ${Math.floor(72 - elapsedHours)}h remaining. UM Department Manager has been notified.`,
    },
    code_red: {
      bg: 'bg-[#3d0f0f]/60 border-[#ef4444]',
      text: 'text-[#ef4444]',
      label: 'SLA Code Red',
      detail: `Case ${caseId} has been active for ${Math.floor(elapsedHours)}h. ${Math.floor(72 - elapsedHours)}h remaining. Case has been re-routed to High Priority / Any Available Specialist queue. UM Department Manager notified.`,
    },
  }[level] ?? {
    bg: 'bg-[#1e2d4a] border-[#3b82f6]',
    text: 'text-[#3b82f6]',
    label: 'SLA Notice',
    detail: '',
  };

  return (
    <div
      className={`w-full border-y ${config.bg} px-6 py-3`}
      role="alert"
      aria-live={level === 'code_red' ? 'assertive' : 'polite'}
    >
      <div className="mx-auto max-w-screen-2xl flex items-center gap-3">
        <span className={`text-sm font-bold ${config.text}`}>{config.label}</span>
        <span className="text-sm text-[#8899bb]">{config.detail}</span>
      </div>
    </div>
  );
};
