// frontend/src/App.tsx
// Step 15 — Root application component
// Routes between SessionInitForm (pre-session) and WorkflowPage (active session)

import { useState } from 'react';
import { SessionInitForm } from './components/SessionInitForm';
import { WorkflowPage } from './pages/WorkflowPage';

interface ActiveSession {
  caseId: string;
  specialistId: string;
  intakeTimestamp: string;
  streamUrl: string;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://65.20.89.119:8000';

function App() {
  const [session, setSession] = useState<ActiveSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSessionInit = async (
    caseId: string,
    specialistId: string,
    sessionToken: string
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/session/initiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          specialist_id: specialistId,
          session_token: sessionToken,
          case_type: 'concurrent_review',
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        setError(err.detail ?? 'Session initiation failed.');
        return;
      }

      const data = await res.json() as { case_id: string; stream_url: string };
      setSession({
        caseId: data.case_id,
        specialistId,
        intakeTimestamp: new Date().toISOString(),
        streamUrl: data.stream_url,
      });
    } catch (e) {
      setError(`Connection error: ${String(e)}. Is the Bridge-PA server running?`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!session) {
    return (
      <SessionInitForm
        onSubmit={handleSessionInit}
        isLoading={isLoading}
        error={error}
      />
    );
  }

  return (
    <WorkflowPage
      caseId={session.caseId}
      specialistId={session.specialistId}
      intakeTimestamp={session.intakeTimestamp}
    />
  );
}

export default App;
