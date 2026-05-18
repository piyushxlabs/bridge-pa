// frontend/src/components/Header.tsx
// Step 15 — Header Bar
// Spec: Case ID, Specialist ID, mode badge, SLA timer, Emergency Stop button

import React from 'react';
import { AlertTriangle, Clock, Shield } from 'lucide-react';
import type { WorkflowMode, AlertLevel } from '../types/events';
import { useSLATimer } from '../hooks/useSLATimer';

interface HeaderProps {
  caseId: string;
  specialistId: string;
  mode: WorkflowMode;
  intakeTimestamp: string | null;
  slaAlertLevel: AlertLevel | null;
  isEmergencyStop: boolean;
  onEmergencyStop: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  caseId,
  specialistId,
  mode,
  intakeTimestamp,
  slaAlertLevel,
  isEmergencyStop,
  onEmergencyStop,
}) => {
  const sla = useSLATimer(intakeTimestamp);

  const slaBarColor = sla.isCodeRed
    ? '#ef4444'
    : sla.isCritical
    ? '#f97316'
    : sla.isWarning
    ? '#f59e0b'
    : '#3b82f6';

  const modeBadge = () => {
    if (isEmergencyStop) return <span className="badge-emergency">⛔ EMERGENCY STOP</span>;
    if (mode === 'mode_a') return <span className="badge-mode-a">✓ Mode A — Autonomous</span>;
    if (mode === 'mode_b') return <span className="badge-mode-b">⚡ Mode B — Specialist Review</span>;
    if (mode === 'suspended') return <span className="badge-waiting">⏸ AWAITING SPECIALIST ACTION</span>;
    return <span className="inline-flex items-center rounded-full bg-[#1e2d4a] px-3 py-0.5 text-xs font-medium text-[#8899bb]">Semi-Autonomous</span>;
  };

  return (
    <header className="sticky top-0 z-50 border-b border-[#1e2d4a] bg-[#0a0f1e]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-screen-2xl items-center justify-between gap-4 px-6 py-3">
        {/* Left: Branding + Case Info */}
        <div className="flex items-center gap-4 min-w-0">
          <div className="flex items-center gap-2 text-[#3b82f6]">
            <Shield size={20} className="shrink-0" />
            <span className="font-semibold text-sm tracking-wide text-[#e2e8f8] whitespace-nowrap">Bridge-PA</span>
          </div>
          <div className="h-5 w-px bg-[#1e2d4a]" />
          <div className="min-w-0">
            <p className="text-xs text-[#4a5f82] font-medium uppercase tracking-wider">Case ID</p>
            <p className="text-sm font-mono font-semibold text-[#e2e8f8] truncate">{caseId || '—'}</p>
          </div>
          <div className="h-5 w-px bg-[#1e2d4a]" />
          <div className="hidden sm:block min-w-0">
            <p className="text-xs text-[#4a5f82] font-medium uppercase tracking-wider">Specialist</p>
            <p className="text-sm font-mono text-[#8899bb] truncate">{specialistId || '—'}</p>
          </div>
        </div>

        {/* Center: Mode Badge */}
        <div className="flex items-center gap-3">
          {modeBadge()}
        </div>

        {/* Right: SLA Timer + Emergency Stop */}
        <div className="flex items-center gap-4 shrink-0">
          {/* SLA Counter */}
          {intakeTimestamp && (
            <div className="hidden md:block text-right">
              <div className="flex items-center gap-1.5 text-xs text-[#4a5f82] mb-1">
                <Clock size={11} />
                <span>SLA {sla.elapsed} / 72:00:00</span>
                {slaAlertLevel === 'code_red' && <span className="text-[#ef4444] font-semibold">CODE RED</span>}
                {slaAlertLevel === 'critical' && <span className="text-[#f97316] font-semibold">CRITICAL</span>}
                {slaAlertLevel === 'standard' && <span className="text-[#f59e0b] font-semibold">WARNING</span>}
              </div>
              <div className="sla-bar-track w-36">
                <div
                  className="sla-bar-fill"
                  style={{ width: `${sla.percentUsed}%`, backgroundColor: slaBarColor }}
                />
              </div>
            </div>
          )}

          {/* Emergency Stop Button */}
          <button
            id="emergency-stop-btn"
            className="btn-emergency"
            onClick={onEmergencyStop}
            aria-label="Trigger Emergency Stop — halt all workflow processing"
            disabled={isEmergencyStop}
          >
            <AlertTriangle size={14} />
            <span className="hidden sm:inline">Emergency Stop</span>
          </button>
        </div>
      </div>
    </header>
  );
};
