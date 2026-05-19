// frontend/src/pages/WorkflowPage.tsx
// Step 15 — Main workflow execution monitor page
// Three-panel: Header / Center timeline / Right sidebar Activity Log

import React, { useState, useCallback, useRef } from 'react';
import { Header } from '../components/Header';
import { StepCard } from '../components/StepCard';
import { WhitelistTable } from '../components/WhitelistTable';
import { ModeBReviewPanel } from '../components/ModeBReviewPanel';
import { ActivityLog } from '../components/ActivityLog';
import { EmergencyStopBanner, SLAAlertBanner } from '../components/EmergencyStopBanner';
import { useSSEStream } from '../hooks/useSSEStream';
import { useWebSocket } from '../hooks/useWebSocket';
import type {
  SSEEvent,
  WorkflowStep,
  WorkflowMode,
  AlertLevel,
  SpecialistActionType,
} from '../types/events';
import { INITIAL_WORKFLOW_STEPS } from '../types/events';
import type { ActivityLogEntry } from '../components/ActivityLog';

interface WorkflowPageProps {
  caseId: string;
  specialistId: string;
  intakeTimestamp: string;
}

export const WorkflowPage: React.FC<WorkflowPageProps> = ({
  caseId,
  specialistId,
  intakeTimestamp,
}) => {
  const [steps, setSteps] = useState<WorkflowStep[]>(INITIAL_WORKFLOW_STEPS);
  const [mode, setMode] = useState<WorkflowMode>(null);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [conditionResults, setConditionResults] = useState<Record<string, boolean>>({});
  const [escalationCodes, setEscalationCodes] = useState<string[]>([]);
  const [slaAlertLevel, setSlaAlertLevel] = useState<AlertLevel | null>(null);
  const [isEmergencyStop, setIsEmergencyStop] = useState(false);
  const [emergencyDetail, setEmergencyDetail] = useState<{ reason: string; scope: string; timestamp: string } | null>(null);
  const [connectionLost, setConnectionLost] = useState(false);
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const logIdRef = useRef(0);

  // ── WebSocket for Mode B ──────────────────────────────────────────────────
  const isModeBActive = mode === 'mode_b' || mode === 'suspended';
  const { sendAction, packageData, escalationCodes: wsEscalationCodes } = useWebSocket(
    isModeBActive ? caseId : null
  );

  // ── Activity log helper ────────────────────────────────────────────────────
  const addLog = useCallback((category: string, message: string, agent = 'system', timestamp?: string) => {
    logIdRef.current += 1;
    const entry: ActivityLogEntry = {
      id: String(logIdRef.current),
      timestamp: timestamp ?? new Date().toISOString(),
      category,
      message,
      agent,
    };
    setActivityLog(prev => [...prev, entry]);
  }, []);

  // ── SSE event dispatcher ───────────────────────────────────────────────────
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    const { data } = event;

    switch (event.event) {
      case 'step_status': {
        const { step_number, step_name, status, agent, error, timestamp } = data as { step_number: number; step_name: string; status: string; agent: string; error?: string; timestamp: string };
        setSteps(prev =>
          prev.map(s =>
            s.number === step_number
              ? { ...s, status: status as WorkflowStep['status'], timestamp, error }
              : s
          )
        );
        addLog('session', `Step ${step_number} (${step_name}): ${status}`, agent, timestamp);
        break;
      }

      case 'whitelist_conditions': {
        const { condition_results, escalation_reason_codes, timestamp } = data as { condition_results: Record<string, boolean>; escalation_reason_codes: string[]; timestamp: string };
        setConditionResults(condition_results);
        setEscalationCodes(escalation_reason_codes);
        addLog('evaluation', 'Whitelist condition evaluation complete', 'criteria_evaluation', timestamp);
        break;
      }

      case 'routing_decision': {
        const { mode: m, timestamp } = data as { mode: string; timestamp: string };
        setMode(m as WorkflowMode);
        addLog('session', `Routing decision: ${m === 'mode_a' ? 'Mode A — Autonomous Execution' : 'Mode B — Specialist Review Required'}`, 'workflow_supervisor', timestamp);
        break;
      }

      case 'emergency_stop': {
        const { reason, scope, timestamp } = data as { reason: string; scope: string; timestamp: string };
        setIsEmergencyStop(true);
        setEmergencyDetail({ reason, scope, timestamp });
        addLog('admin', `Emergency Stop triggered. Scope: ${scope}. Reason: ${reason}`, 'system', timestamp);
        break;
      }

      case 'sla_alert': {
        const { alert_level, elapsed_hours, timestamp } = data as { alert_level: AlertLevel; elapsed_hours: number; timestamp: string };
        setSlaAlertLevel(alert_level);
        addLog('sla', `SLA Alert — ${alert_level}: ${Math.floor(elapsed_hours)}h elapsed`, 'sla_monitor', timestamp);
        break;
      }

      case 'activity_log_entry': {
        const { category, message, agent, timestamp } = data as { category: string; message: string; agent: string; timestamp: string };
        addLog(category, message, agent, timestamp);
        break;
      }

      default:
        break;
    }
  }, [addLog]);

  useSSEStream({
    caseId,
    onEvent: handleSSEEvent,
    onConnectionLost: () => {
      setConnectionLost(true);
      addLog('session', 'SSE connection lost — attempting to reconnect...');
    },
    onReconnected: () => {
      setConnectionLost(false);
      addLog('session', 'SSE connection restored.');
    },
  });

  // ── Toggle step card expansion ─────────────────────────────────────────────
  const handleToggleStep = useCallback((stepNumber: number) => {
    setSteps(prev =>
      prev.map(s => s.number === stepNumber ? { ...s, expanded: !s.expanded } : s)
    );
  }, []);

  // ── Emergency Stop handler ─────────────────────────────────────────────────
  const handleEmergencyStop = useCallback(async () => {
    const token = prompt('Enter UM Manager Token to confirm Emergency Stop:');
    if (!token) return;
    try {
      const apiBase = (import.meta.env.VITE_API_URL as string) || 'http://65.20.89.119:8000';
      const res = await fetch(`${apiBase}/admin/emergency-stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Manager-Token': token },
        body: JSON.stringify({ case_id: caseId, scope: 'case', reason: 'Specialist-triggered emergency stop' }),
      });
      if (!res.ok) {
        const err = await res.json();
        addLog('admin', `Emergency Stop failed: ${err.detail ?? res.status}`);
      }
    } catch (e) {
      addLog('admin', `Emergency Stop request error: ${String(e)}`);
    }
  }, [caseId, addLog]);

  // ── Mode B Specialist Action ───────────────────────────────────────────────
  const handleSpecialistAction = useCallback((action: SpecialistActionType, rationale: string) => {
    setIsSubmittingAction(true);
    sendAction({ action_type: action, rationale });
    setMode('suspended');
    addLog('session', `Specialist action submitted: ${action}`, specialistId);
    setIsSubmittingAction(false);
  }, [sendAction, specialistId, addLog]);

  // ── Find the active step (first in_progress) ──────────────────────────────
  const activeStepNumber = steps.find(s => s.status === 'in_progress')?.number;

  // ── Determine whether whitelist table should show ─────────────────────────
  const step5 = steps.find(s => s.number === 5);
  const showWhitelist = step5?.status === 'completed' && Object.keys(conditionResults).length > 0;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#0a0f1e]">
      {/* ── Header ─────────────────────────────────────────────── */}
      <Header
        caseId={caseId}
        specialistId={specialistId}
        mode={mode}
        intakeTimestamp={intakeTimestamp}
        slaAlertLevel={slaAlertLevel}
        isEmergencyStop={isEmergencyStop}
        onEmergencyStop={handleEmergencyStop}
      />

      {/* ── System banners (stack below header) ────────────────── */}
      {isEmergencyStop && emergencyDetail && (
        <EmergencyStopBanner
          reason={emergencyDetail.reason}
          scope={emergencyDetail.scope}
          timestamp={emergencyDetail.timestamp}
          caseId={caseId}
        />
      )}
      {slaAlertLevel && !isEmergencyStop && (
        <SLAAlertBanner level={slaAlertLevel} caseId={caseId} elapsedHours={0} />
      )}
      {connectionLost && (
        <div className="w-full border-y border-[#3b82f6]/30 bg-[#1d3f7a]/20 px-6 py-2 text-xs text-[#3b82f6] text-center" role="status">
          Connection lost — attempting to reconnect...
        </div>
      )}

      {/* ── Main body: Center + Sidebar ─────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Center Panel ────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto p-5 space-y-3">
          {/* Mode B: Replace timeline with review panel */}
          {isModeBActive && packageData ? (
            <ModeBReviewPanel
              caseId={caseId}
              packageData={packageData}
              escalationCodes={wsEscalationCodes.length ? wsEscalationCodes : escalationCodes}
              conditionResults={conditionResults}
              onSubmitAction={handleSpecialistAction}
              isSubmitting={isSubmittingAction}
            />
          ) : (
            <>
              {/* Connection status hint */}
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-sm font-semibold text-[#8899bb]">Workflow Timeline</h2>
                <span className="text-xs text-[#4a5f82]">
                  {steps.filter(s => s.status === 'completed').length} / {steps.length} steps complete
                </span>
              </div>

              {/* Step cards */}
              {steps.map(step => (
                <React.Fragment key={step.number}>
                  <StepCard
                    step={step}
                    onToggle={handleToggleStep}
                    isActive={step.number === activeStepNumber}
                  />
                  {/* Whitelist table inline under Step 5 */}
                  {step.number === 5 && showWhitelist && (
                    <div className="pl-10">
                      <WhitelistTable
                        conditionResults={conditionResults}
                        escalationCodes={escalationCodes}
                        determination={mode}
                      />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </>
          )}
        </main>

        {/* ── Right Sidebar: Activity Log ──────────────────────────── */}
        <aside className="hidden lg:flex w-80 xl:w-96 flex-col border-l border-[#1e2d4a] bg-[#0f1629] overflow-hidden">
          <ActivityLog entries={activityLog} />
        </aside>
      </div>
    </div>
  );
};
