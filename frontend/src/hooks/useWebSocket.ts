// frontend/src/hooks/useWebSocket.ts
// Step 15 — WebSocket Hook for Mode B Specialist Approval Gate

import { useEffect, useRef, useCallback, useState } from 'react';
import type { SpecialistActionType } from '../types/events';

interface SpecialistAction {
  action_type: SpecialistActionType;
  rationale: string;
}

interface UseWebSocketReturn {
  sendAction: (action: SpecialistAction) => void;
  isConnected: boolean;
  packageData: Record<string, unknown> | null;
  escalationCodes: string[];
}

export function useWebSocket(
  caseId: string | null,
  baseUrl = 'ws://localhost:8000'
): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [packageData, setPackageData] = useState<Record<string, unknown> | null>(null);
  const [escalationCodes, setEscalationCodes] = useState<string[]>([]);

  useEffect(() => {
    if (!caseId) return;

    const url = `${baseUrl}/workflow/${caseId}/action`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data as string);
        if (payload.event === 'mode_b_package') {
          setPackageData(payload.recommendation_package ?? {});
          setEscalationCodes(payload.escalation_reason_codes ?? []);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
    };

    ws.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [caseId, baseUrl]);

  const sendAction = useCallback((action: SpecialistAction) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(action));
    }
  }, []);

  return { sendAction, isConnected, packageData, escalationCodes };
}
