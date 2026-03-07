import { useState, useEffect } from 'react';
import { getEvents } from '../services/api';

const typeColors = {
  ANOMALY: 'text-red',
  REROUTE: 'text-amber',
  ALERT: 'text-red',
  LEARNING: 'text-purple',
  APPROVAL: 'text-amber',
  EXECUTE: 'text-green',
  OPTIMIZE: 'text-blue',
};

export default function EventTicker() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    getEvents().then(setEvents);
    const id = setInterval(() => getEvents().then(setEvents), 10000);
    return () => clearInterval(id);
  }, []);

  if (!events.length) {
    return (
      <div className="w-full bg-surface border-b border-border overflow-hidden h-9 flex items-center shadow-sm px-6">
        <span className="text-[10px] text-muted/50 font-mono">No agent activity yet — run a simulation to see live events here</span>
      </div>
    );
  }

  const doubled = [...events, ...events];

  return (
    <div className="w-full bg-surface border-b border-border overflow-hidden h-9 flex items-center shadow-sm">
      <div className="flex animate-ticker whitespace-nowrap">
        {doubled.map((e, i) => (
          <span key={i} className="inline-flex items-center gap-2 px-6 text-xs font-mono">
            <span className="text-muted">{e.time}</span>
            <span className="text-border">•</span>
            <span className={`font-semibold ${typeColors[e.type] || 'text-text'}`}>{e.type}</span>
            <span className="text-muted/50">{e.flow}</span>
            <span className="text-text/70">{e.message}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
