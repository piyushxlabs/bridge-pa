// frontend/src/components/ModeBReviewPanel.tsx
// Step 15 — Mode B Full Recommendation Package Review Panel
// Spec: Full-panel, non-dismissible until specialist action, never collapsed

import React, { useState } from 'react';
import { FileText, ShieldAlert, Send, Edit3, XOctagon } from 'lucide-react';
import { WhitelistTable } from './WhitelistTable';
import type { SpecialistActionType } from '../types/events';

interface ModeBReviewPanelProps {
  caseId: string;
  packageData: Record<string, unknown>;
  escalationCodes: string[];
  conditionResults: Record<string, boolean>;
  onSubmitAction: (action: SpecialistActionType, rationale: string) => void;
  isSubmitting: boolean;
}

export const ModeBReviewPanel: React.FC<ModeBReviewPanelProps> = ({
  caseId,
  packageData,
  escalationCodes,
  conditionResults,
  onSubmitAction,
  isSubmitting,
}) => {
  const [selectedAction, setSelectedAction] = useState<SpecialistActionType | null>(null);
  const [rationale, setRationale] = useState('');
  const [confirmStep, setConfirmStep] = useState(false);

  const handleActionSelect = (action: SpecialistActionType) => {
    if (action === 'approved') {
      // Approve doesn't require rationale confirmation step
      onSubmitAction('approved', 'Specialist approved recommendation.');
      return;
    }
    setSelectedAction(action);
    setConfirmStep(true);
    setRationale('');
  };

  const handleConfirm = () => {
    if (!selectedAction || rationale.trim().length === 0) return;
    onSubmitAction(selectedAction, rationale.trim());
  };

  const pkg = packageData ?? {};

  return (
    <div
      className="rounded-2xl border-2 border-[#f59e0b]/40 bg-[#0f1629] overflow-hidden shadow-[0_0_40px_rgba(245,158,11,0.12)]"
      role="main"
      aria-label="Mode B Specialist Review Panel"
      aria-live="assertive"
    >
      {/* Panel Header */}
      <div className="border-b border-[#f59e0b]/30 bg-[#3d2a00]/30 px-6 py-4">
        <div className="flex items-center gap-3">
          <ShieldAlert size={22} className="text-[#f59e0b]" />
          <div>
            <h2 className="text-lg font-bold text-[#f59e0b]">Specialist Review Required — Mode B</h2>
            <p className="text-xs text-[#8899bb] mt-0.5">
              Case {caseId} · Full Recommendation Package — all fields presented. No content is collapsed.
            </p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6 max-h-[calc(100vh-260px)] overflow-y-auto">

        {/* Case Metadata */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#4a5f82] mb-3 flex items-center gap-2">
            <FileText size={13} /> Case Metadata
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {([
              ['Case ID', caseId],
              ['Case Type', String(pkg.case_type ?? 'Concurrent Review')],
              ['Interqual Set', String(pkg.criteria_set ?? '—')],
              ['Match Type', String(pkg.match_type ?? '—')],
              ['Intake Source', String(pkg.intake_source_ref ?? '—')],
              ['Session', String(pkg.session_id ?? '—')],
            ] as [string, string][]).map(([label, value]) => (
              <div key={label} className="rounded-lg bg-[#0a0f1e] border border-[#1e2d4a] p-3">
                <p className="text-[10px] font-medium uppercase tracking-wider text-[#4a5f82]">{label}</p>
                <p className="text-sm font-mono text-[#e2e8f8] mt-0.5 truncate">{value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Recommendation */}
        {Boolean(pkg.recommendation) && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#4a5f82] mb-3">Criteria-Based Recommendation</h3>
            <div className="rounded-xl border border-[#1e2d4a] bg-[#0a0f1e] p-4">
              <p className="text-sm text-[#e2e8f8]">{String(pkg.recommendation)}</p>
              <p className="mt-3 text-xs text-[#4a5f82] italic border-t border-[#1e2d4a] pt-3">
                This package does not include a clinical necessity determination. The specialist retains full clinical authority.
              </p>
            </div>
          </section>
        )}

        {/* Whitelist Conditions — always visible */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#4a5f82] mb-1">
            Whitelist Condition Results (All 7)
          </h3>
          <WhitelistTable
            conditionResults={conditionResults}
            escalationCodes={escalationCodes}
            determination="mode_b"
          />
        </section>

        {/* PHI Note */}
        <div className="rounded-lg border border-[#1e2d4a] bg-[#0a0f1e] p-3 text-xs text-[#4a5f82] italic">
          PHI field values and credential values are not displayed in this interface. Audit logging of all PHI interactions is confirmed via the Veea Lobster Trap audit proxy.
        </div>
      </div>

      {/* Action Panel — always pinned at bottom */}
      <div className="border-t border-[#1e2d4a] bg-[#0a0f1e] px-6 py-4">
        {!confirmStep ? (
          <div>
            <p className="text-sm font-medium text-[#e2e8f8] mb-3">Select your action:</p>
            <div className="flex flex-wrap gap-3">
              <button id="btn-approve" className="btn-approve" onClick={() => handleActionSelect('approved')} disabled={isSubmitting}>
                <Send size={14} /> Approve
              </button>
              <button id="btn-modify" className="btn-modify" onClick={() => handleActionSelect('modified')} disabled={isSubmitting}>
                <Edit3 size={14} /> Modify
              </button>
              <button id="btn-override" className="btn-override" onClick={() => handleActionSelect('overridden')} disabled={isSubmitting}>
                <XOctagon size={14} /> Override
              </button>
            </div>
            <p className="text-xs text-[#4a5f82] mt-2">
              Each action requires a deliberate click. No defaults are pre-selected.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className={`rounded-lg border p-3 text-sm font-semibold
              ${selectedAction === 'modified' ? 'border-[#f59e0b]/40 bg-[#3d2a00]/30 text-[#f59e0b]' : 'border-[#ef4444]/40 bg-[#3d0f0f]/30 text-[#ef4444]'}`}>
              Confirm: {selectedAction === 'modified' ? 'Modify pre-populated fields' : 'Override — specialist clinical determination supersedes recommendation. No resubmission will occur.'}
            </div>
            <div>
              <label htmlFor="rationale-input" className="block text-xs font-medium text-[#8899bb] mb-1">
                Rationale <span className="text-[#ef4444]">*</span> (required)
              </label>
              <textarea
                id="rationale-input"
                className="w-full rounded-lg border border-[#1e2d4a] bg-[#0a0f1e] p-3 text-sm text-[#e2e8f8] focus:outline-none focus:border-[#3b82f6] resize-none"
                rows={3}
                value={rationale}
                onChange={e => setRationale(e.target.value)}
                placeholder="Enter rationale for this action..."
                aria-required="true"
              />
            </div>
            <div className="flex gap-3">
              <button
                id="btn-confirm-action"
                className="btn-primary"
                onClick={handleConfirm}
                disabled={rationale.trim().length === 0 || isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Confirm & Submit'}
              </button>
              <button
                className="btn-primary bg-transparent border border-[#1e2d4a] text-[#8899bb] hover:bg-[#141c35]"
                onClick={() => { setConfirmStep(false); setSelectedAction(null); setRationale(''); }}
                disabled={isSubmitting}
              >
                Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
