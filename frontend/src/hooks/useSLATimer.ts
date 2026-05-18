// frontend/src/hooks/useSLATimer.ts
// Step 15 — Live SLA Timer
// Ticks every second, displays elapsed hours against 72h CMS deadline.

import { useState, useEffect, useRef } from 'react';

interface SLATimerResult {
  elapsed: string;     // "HH:MM:SS"
  elapsedHours: number;
  percentUsed: number; // 0–100
  isWarning: boolean;  // >48h
  isCritical: boolean; // >60h
  isCodeRed: boolean;  // >66h
}

const CMS_DEADLINE_HOURS = 72;

export function useSLATimer(intakeTimestamp: string | null): SLATimerResult {
  const intakeMs = intakeTimestamp ? new Date(intakeTimestamp).getTime() : null;
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const compute = (): SLATimerResult => {
    if (!intakeMs) {
      return { elapsed: '00:00:00', elapsedHours: 0, percentUsed: 0, isWarning: false, isCritical: false, isCodeRed: false };
    }
    const diffMs = Date.now() - intakeMs;
    const totalSeconds = Math.max(0, Math.floor(diffMs / 1000));
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    const elapsed = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    const elapsedHours = diffMs / 3_600_000;
    const percentUsed = Math.min(100, (elapsedHours / CMS_DEADLINE_HOURS) * 100);
    return {
      elapsed,
      elapsedHours,
      percentUsed,
      isWarning: elapsedHours >= 48,
      isCritical: elapsedHours >= 60,
      isCodeRed: elapsedHours >= 66,
    };
  };

  const [result, setResult] = useState<SLATimerResult>(compute);

  useEffect(() => {
    if (!intakeMs) return;
    intervalRef.current = setInterval(() => setResult(compute()), 1000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intakeMs]);

  return result;
}
