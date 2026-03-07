import { Activity } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="w-full bg-surface border-t border-amber/10 px-4 py-1.5 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green" />
          <span className="text-[10px] text-text/30 font-mono">SYSTEM NOMINAL</span>
        </div>
        <span className="text-text/10">|</span>
        <span className="text-[10px] text-text/20 font-mono">LATENCY 12ms</span>
        <span className="text-text/10">|</span>
        <span className="text-[10px] text-text/20 font-mono">UPTIME 99.97%</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-[10px] text-text/20 font-mono">AGENTS 5/5</span>
        <span className="text-text/10">|</span>
        <span className="text-[10px] text-text/20 font-mono">OLLAMA CONNECTED</span>
        <span className="text-text/10">|</span>
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3 text-amber/40" />
          <span className="text-[10px] text-text/20 font-mono">CHAINMIND v2.4.1</span>
        </div>
      </div>
    </footer>
  );
}
