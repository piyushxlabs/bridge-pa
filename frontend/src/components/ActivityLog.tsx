// frontend/src/components/ActivityLog.tsx
// Step 15 — Right sidebar chronological activity log

import React, { useEffect, useRef } from 'react';
import { Activity, User, Bot, Zap, AlertTriangle } from 'lucide-react';

export interface ActivityLogEntry {
  id: string;
  timestamp: string;
  category: string;
  message: string;
  agent: string;
}

interface ActivityLogProps {
  entries: ActivityLogEntry[];
}

const CATEGORY_ICON: Record<string, React.ReactNode> = {
  audit:      <Bot size={11} className="text-[#3b82f6]" />,
  tool:       <Zap size={11} className="text-[#8899bb]" />,
  session:    <User size={11} className="text-[#10b981]" />,
  sla:        <AlertTriangle size={11} className="text-[#f59e0b]" />,
  admin:      <AlertTriangle size={11} className="text-[#ef4444]" />,
  evaluation: <Bot size={11} className="text-[#a78bfa]" />,
  default:    <Activity size={11} className="text-[#4a5f82]" />,
};

const CATEGORY_COLOR: Record<string, string> = {
  audit:      'bg-[#1d3f7a]/40 text-[#3b82f6]',
  tool:       'bg-[#1e2d4a] text-[#8899bb]',
  session:    'bg-[#0a3d2a] text-[#10b981]',
  sla:        'bg-[#3d2a00] text-[#f59e0b]',
  admin:      'bg-[#3d0f0f] text-[#ef4444]',
  evaluation: 'bg-[#2d1f4a] text-[#a78bfa]',
  default:    'bg-[#1e2d4a] text-[#4a5f82]',
};

export const ActivityLog: React.FC<ActivityLogProps> = ({ entries }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [entries.length]);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="shrink-0 border-b border-[#1e2d4a] px-4 py-3">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-[#3b82f6]" />
          <h2 className="text-sm font-semibold text-[#e2e8f8]">Activity Log</h2>
          <span className="ml-auto text-xs font-mono text-[#4a5f82]">{entries.length} events</span>
        </div>
      </div>

      {/* Entries */}
      <div className="flex-1 overflow-y-auto px-3 py-2" role="log" aria-live="polite" aria-label="Case activity log">
        {entries.length === 0 && (
          <p className="py-6 text-center text-xs text-[#4a5f82]">No events yet. Workflow events will appear here in real time.</p>
        )}
        {entries.map((entry) => {
          const cat = entry.category in CATEGORY_ICON ? entry.category : 'default';
          const absTime = new Date(entry.timestamp).toLocaleTimeString();
          return (
            <div key={entry.id} className="log-entry">
              <div className="shrink-0 pt-0.5">
                {CATEGORY_ICON[cat]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-[#e2e8f8] leading-snug">{entry.message}</p>
                <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                  <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium ${CATEGORY_COLOR[cat]}`}>
                    {entry.category}
                  </span>
                  <span className="text-[10px] text-[#4a5f82] font-mono">{absTime}</span>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
