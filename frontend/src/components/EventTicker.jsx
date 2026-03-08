import { useState, useEffect, useRef } from 'react';
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

/* Consistent scroll speed regardless of content length */
const SCROLL_SPEED_PX_PER_SEC = 60;

export default function EventTicker() {
  const [events, setEvents] = useState([]);
  const [duration, setDuration] = useState(30);
  const trackRef = useRef(null);

  useEffect(() => {
    getEvents().then(setEvents);
    const id = setInterval(() => getEvents().then(setEvents), 10000);
    return () => clearInterval(id);
  }, []);

  /* Recalculate duration whenever events change so speed stays constant */
  useEffect(() => {
    if (!trackRef.current || events.length === 0) return;
    // Small delay to let the DOM render so scrollWidth is accurate
    const frame = requestAnimationFrame(() => {
      const halfWidth = trackRef.current.scrollWidth / 2;
      const secs = Math.max(10, halfWidth / SCROLL_SPEED_PX_PER_SEC);
      setDuration(secs);
    });
    return () => cancelAnimationFrame(frame);
  }, [events]);

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
      <div
        ref={trackRef}
        className="flex whitespace-nowrap"
        style={{
          animation: `ticker ${duration}s linear infinite`,
        }}
      >
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
