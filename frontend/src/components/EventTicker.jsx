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

  if (!events.length) return null;

  const doubled = [...events, ...events];

  return (
    <div className="w-full bg-surface/80 border-b border-amber/10 overflow-hidden h-8 flex items-center">
      <div className="flex animate-ticker whitespace-nowrap">
        {doubled.map((e, i) => (
          <span key={i} className="inline-flex items-center gap-2 px-6 text-xs font-mono">
            <span className="text-text/40">{e.time}</span>
            <span className="text-amber/30">•</span>
            <span className={`font-semibold ${typeColors[e.type] || 'text-text'}`}>{e.type}</span>
            <span className="text-text/30">{e.flow}</span>
            <span className="text-text/70">{e.message}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
