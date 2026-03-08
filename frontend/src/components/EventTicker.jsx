import { useState, useEffect, useRef, useCallback } from 'react';
import { getEvents } from '../services/api';

const typeColors = {
  ANOMALY: 'text-red',
  REROUTE: 'text-amber',
  ALERT: 'text-red',
  LEARNING: 'text-purple',
  APPROVAL: 'text-amber',
  EXECUTE: 'text-green',
  OPTIMIZE: 'text-blue',
  MONITOR: 'text-slate',
};

const SCROLL_SPEED_PX_PER_SEC = 50;

export default function EventTicker() {
  const [events, setEvents] = useState([]);
  const wrapperRef = useRef(null);
  const trackRef = useRef(null);
  const styleRef = useRef(null);

  useEffect(() => {
    getEvents().then(setEvents);
    const id = setInterval(() => getEvents().then(setEvents), 10000);
    return () => clearInterval(id);
  }, []);

  /* Inject / update a <style> tag so we never re-trigger the animation on data change */
  const syncDuration = useCallback(() => {
    if (!trackRef.current) return;
    const halfWidth = trackRef.current.scrollWidth / 2;
    if (halfWidth < 50) return;
    const secs = Math.max(15, halfWidth / SCROLL_SPEED_PX_PER_SEC);

    if (!styleRef.current) {
      styleRef.current = document.createElement('style');
      document.head.appendChild(styleRef.current);
    }
    styleRef.current.textContent = `
      @keyframes ticker-scroll {
        0%   { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-50%, 0, 0); }
      }
      .ticker-track {
        will-change: transform;
        animation: ticker-scroll ${secs}s linear infinite;
      }
    `;
  }, []);

  useEffect(() => {
    if (events.length === 0) return;
    // wait one frame for DOM to paint new items
    const raf = requestAnimationFrame(syncDuration);
    return () => cancelAnimationFrame(raf);
  }, [events, syncDuration]);

  // Cleanup style tag on unmount
  useEffect(() => {
    return () => {
      if (styleRef.current) {
        styleRef.current.remove();
        styleRef.current = null;
      }
    };
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
    <div
      ref={wrapperRef}
      className="w-full bg-surface border-b border-border overflow-hidden h-9 flex items-center shadow-sm"
    >
      <div ref={trackRef} className="ticker-track flex whitespace-nowrap">
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
