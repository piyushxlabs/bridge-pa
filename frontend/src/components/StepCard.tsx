// frontend/src/components/StepCard.tsx
// Step 15 — Single workflow step card with expandable tool detail

import React from 'react';
import { CheckCircle, XCircle, Loader2, Clock, ChevronDown, ChevronRight, AlertCircle, PauseCircle } from 'lucide-react';
import type { WorkflowStep } from '../types/events';

interface StepCardProps {
  step: WorkflowStep;
  onToggle: (stepNumber: number) => void;
  isActive: boolean;
}

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending:    <div className="w-2 h-2 rounded-full dot-pending" />,
  in_progress:<Loader2 size={16} className="text-[#3b82f6] animate-spin" />,
  completed:  <CheckCircle size={16} className="text-[#10b981]" />,
  failed:     <XCircle size={16} className="text-[#ef4444]" />,
  suspended:  <PauseCircle size={16} className="text-[#f59e0b] animate-pulse" />,
};

const STATUS_TEXT: Record<string, string> = {
  pending:    'Pending',
  in_progress:'In Progress',
  completed:  'Completed',
  failed:     'Failed',
  suspended:  'Suspended — Awaiting Specialist Action',
};

const STEP_BORDER: Record<string, string> = {
  pending:    'step-pending',
  in_progress:'step-progress',
  completed:  'step-completed',
  failed:     'step-failed',
  suspended:  'step-suspended',
};

export const StepCard: React.FC<StepCardProps> = ({ step, onToggle, isActive }) => {
  const isExpandable = step.status !== 'pending';

  return (
    <div
      className={`card ${STEP_BORDER[step.status]} transition-all duration-300 ${isActive ? 'ring-1 ring-[#3b82f6]/30' : ''}`}
      role="region"
      aria-label={`Step ${step.number}: ${step.label}`}
    >
      {/* Header row */}
      <div
        className={`flex items-center gap-3 ${isExpandable ? 'cursor-pointer' : ''}`}
        onClick={() => isExpandable && onToggle(step.number)}
        aria-expanded={step.expanded}
        aria-live="polite"
      >
        {/* Step number */}
        <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-bold
          ${step.status === 'completed' ? 'border-[#10b981]/40 bg-[#0a3d2a] text-[#10b981]' :
            step.status === 'in_progress' ? 'border-[#3b82f6]/40 bg-[#1d3f7a]/30 text-[#3b82f6]' :
            step.status === 'failed' ? 'border-[#ef4444]/40 bg-[#3d0f0f]/30 text-[#ef4444]' :
            step.status === 'suspended' ? 'border-[#f59e0b]/40 bg-[#3d2a00]/30 text-[#f59e0b]' :
            'border-[#1e2d4a] bg-[#0a0f1e] text-[#4a5f82]'}`}
        >
          {step.number}
        </div>

        {/* Status icon */}
        <div className="shrink-0" aria-hidden="true">
          {STATUS_ICONS[step.status]}
        </div>

        {/* Step info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-[#e2e8f8]">{step.label}</h3>
            <span className={`text-xs font-medium
              ${step.status === 'completed' ? 'text-[#10b981]' :
                step.status === 'in_progress' ? 'text-[#3b82f6]' :
                step.status === 'failed' ? 'text-[#ef4444]' :
                step.status === 'suspended' ? 'text-[#f59e0b]' :
                'text-[#4a5f82]'}`}
            >
              {STATUS_TEXT[step.status]}
            </span>
          </div>
          <p className="text-xs text-[#4a5f82] mt-0.5 truncate">{step.description}</p>
        </div>

        {/* Timestamp + expand chevron */}
        <div className="flex items-center gap-2 shrink-0 ml-auto">
          {step.timestamp && (
            <div className="hidden sm:flex items-center gap-1 text-xs text-[#4a5f82]">
              <Clock size={10} />
              {new Date(step.timestamp).toLocaleTimeString()}
            </div>
          )}
          {isExpandable && (
            <div className="text-[#4a5f82]">
              {step.expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </div>
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {step.expanded && step.status !== 'pending' && (
        <div className="mt-3 pt-3 border-t border-[#1e2d4a] space-y-2">
          {step.status === 'failed' && step.error && (
            <div className="flex gap-2 rounded-lg bg-[#3d0f0f]/30 border border-[#ef4444]/20 p-3">
              <AlertCircle size={14} className="text-[#ef4444] shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-[#ef4444] mb-0.5">Failure Detail</p>
                <p className="text-xs text-[#cc8888]">{step.error}</p>
              </div>
            </div>
          )}
          <p className="text-xs text-[#4a5f82] italic">
            PHI field values and credential values are not displayed in this interface.
            Audit logging of all PHI interactions is confirmed via the Veea Lobster Trap audit proxy.
          </p>
        </div>
      )}
    </div>
  );
};
