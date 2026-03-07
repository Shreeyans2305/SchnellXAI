import { Activity } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="w-full bg-surface border-t border-border px-6 py-2 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green" />
          <span className="text-[10px] text-muted font-mono">SYSTEM NOMINAL</span>
        </div>
        <span className="text-border">|</span>
        <span className="text-[10px] text-muted/60 font-mono">LATENCY 12ms</span>
        <span className="text-border">|</span>
        <span className="text-[10px] text-muted/60 font-mono">UPTIME 99.97%</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-[10px] text-muted/60 font-mono">AGENTS 5/5</span>
        <span className="text-border">|</span>
        <span className="text-[10px] text-muted/60 font-mono">OLLAMA CONNECTED</span>
        <span className="text-border">|</span>
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3 text-amber/60" />
          <span className="text-[10px] text-muted/60 font-mono">CHAINMIND v2.4.1</span>
        </div>
      </div>
    </footer>
  );
}
