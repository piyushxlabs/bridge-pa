// frontend/src/components/WhitelistTable.tsx
// Step 15 — 7-condition whitelist evaluation table (always visible when Step 5 complete)

import React from 'react';
import { CheckCircle, XCircle } from 'lucide-react';

interface WhitelistTableProps {
  conditionResults: Record<string, boolean>;
  escalationCodes: string[];
  determination: string | null;
}

const CONDITION_LABELS: Record<string, string> = {
  A: 'Criteria Match Exactness',
  B: 'Extraction Completeness',
  C: 'Cost Threshold',
  D: 'Acuity Level',
  E: 'Length of Stay',
  F: 'Payer Configuration Reachability',
  G: 'Baseline Runtime Threshold Integrity',
};

export const WhitelistTable: React.FC<WhitelistTableProps> = ({
  conditionResults,
  escalationCodes,
  determination,
}) => {
  const conditions = Object.entries(CONDITION_LABELS);
  const allMet = determination === 'mode_a';

  return (
    <div className="mt-4 space-y-3">
      {/* Routing Determination Banner */}
      {determination && (
        <div
          className={`flex items-center gap-3 rounded-xl p-4 border font-semibold
            ${allMet
              ? 'bg-[#0a3d2a] border-[#10b981]/40 text-[#10b981]'
              : 'bg-[#3d2a00] border-[#f59e0b]/40 text-[#f59e0b]'
            }`}
          role="alert"
          aria-live="assertive"
        >
          {allMet
            ? <CheckCircle size={20} />
            : <XCircle size={20} />
          }
          <div>
            <p className="text-base font-bold">
              ROUTING DECISION: {allMet ? 'Mode A — Autonomous Execution' : 'Mode B — Specialist Review Required'}
            </p>
            {!allMet && escalationCodes.length > 0 && (
              <p className="text-xs mt-0.5 font-normal opacity-80">
                Escalation: {escalationCodes.join(' · ')}
              </p>
            )}
          </div>
        </div>
      )}

      {/* 7-Condition Table */}
      <div className="rounded-xl border border-[#1e2d4a] overflow-hidden">
        <table className="w-full text-sm" role="table" aria-label="Whitelist condition evaluation results">
          <thead>
            <tr className="border-b border-[#1e2d4a] bg-[#0a0f1e]">
              <th className="px-4 py-2 text-left text-xs font-medium text-[#4a5f82] uppercase tracking-wider w-8">ID</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[#4a5f82] uppercase tracking-wider">Condition</th>
              <th className="px-4 py-2 text-center text-xs font-medium text-[#4a5f82] uppercase tracking-wider w-24">Result</th>
            </tr>
          </thead>
          <tbody>
            {conditions.map(([id, label], idx) => {
              const passed = conditionResults[id] ?? conditionResults[`Condition ${id}`] ?? false;
              const code = escalationCodes.find(c => c.includes(`condition_${id.toLowerCase()}`));
              return (
                <tr
                  key={id}
                  className={`border-b border-[#1e2d4a]/50 last:border-0 transition-colors
                    ${idx % 2 === 0 ? 'bg-[#0f1629]' : 'bg-[#0a0f1e]'}
                    ${!passed ? 'bg-[#3d2a00]/20' : ''}`}
                >
                  <td className="px-4 py-3 font-mono font-bold text-[#8899bb]">{id}</td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-[#e2e8f8]">{label}</p>
                    {!passed && code && (
                      <p className="text-xs text-[#f59e0b]/70 mt-0.5 font-mono">{code}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {passed
                      ? <span className="inline-flex items-center gap-1 text-[#10b981] font-semibold text-xs"><CheckCircle size={13} />PASS</span>
                      : <span className="inline-flex items-center gap-1 text-[#ef4444] font-semibold text-xs"><XCircle size={13} />FAIL</span>
                    }
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
