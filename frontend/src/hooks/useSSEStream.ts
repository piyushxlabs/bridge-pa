// frontend/src/hooks/useSSEStream.ts
// Step 15 — SSE Stream Hook
// Connects to GET /workflow/{case_id}/stream and dispatches typed events.

import { useEffect, useRef, useCallback } from 'react';
import type { SSEEvent } from '../types/events';

interface UseSSEStreamOptions {
  caseId: string;
  baseUrl?: string;
  onEvent: (event: SSEEvent) => void;
  onConnectionLost?: () => void;
  onReconnected?: () => void;
  enabled?: boolean;
}

const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

export function useSSEStream({
  caseId,
  baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://65.20.89.119:8000',
  onEvent,
  onConnectionLost,
  onReconnected,
  enabled = true,
}: UseSSEStreamOptions) {
  const esRef = useRef<EventSource | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onEventRef = useRef(onEvent);
  const onConnectionLostRef = useRef(onConnectionLost);
  const onReconnectedRef = useRef(onReconnected);

  useEffect(() => {
    onEventRef.current = onEvent;
    onConnectionLostRef.current = onConnectionLost;
    onReconnectedRef.current = onReconnected;
  }, [onEvent, onConnectionLost, onReconnected]);

  const connect = useCallback(() => {
    if (!caseId || !enabled) return;

    const url = `${baseUrl}/workflow/${caseId}/stream`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => {
      reconnectAttempts.current = 0;
      onReconnectedRef.current?.();
    };

    es.onmessage = (e: MessageEvent) => {
      try {
        const parsed: SSEEvent = JSON.parse(e.data);
        onEventRef.current(parsed);
      } catch {
        // Keepalive comments or malformed data — silently skip
      }
    };

    es.onerror = () => {
      es.close();
      esRef.current = null;
      onConnectionLostRef.current?.();

      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current += 1;
        reconnectTimer.current = setTimeout(() => {
          connect();
        }, RECONNECT_DELAY_MS);
      }
    };
  }, [caseId, baseUrl, enabled]);

  useEffect(() => {
    connect();
    return () => {
      esRef.current?.close();
      esRef.current = null;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);
}
