import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, Clock, Cpu, CheckCircle, Wifi, Zap } from 'lucide-react';
import { getMetrics } from '../services/api';

export default function Navbar() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    getMetrics().then(setMetrics);
    const id = setInterval(() => getMetrics().then(setMetrics), 15000);
    return () => clearInterval(id);
  }, []);

  const cards = metrics
    ? [
        { label: 'Shipments', value: metrics.shipments.value, change: metrics.shipments.change, icon: Activity, color: 'text-blue' },
        { label: 'At Risk', value: metrics.atRisk.value, change: metrics.atRisk.change, icon: AlertTriangle, color: 'text-amber' },
        { label: 'Delayed', value: metrics.delayed.value, change: metrics.delayed.change, icon: Clock, color: 'text-red' },
        { label: 'Agent Ops', value: metrics.agentOps.value.toLocaleString(), change: metrics.agentOps.change, icon: Cpu, color: 'text-purple' },
        { label: 'Approvals', value: metrics.approvals.value, change: metrics.approvals.change, icon: CheckCircle, color: 'text-green' },
      ]
    : [];

  return (
    <nav className="w-full bg-surface border-b border-amber/10 px-4 py-2">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2 mr-6">
          <div className="w-8 h-8 rounded-lg bg-amber/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-amber" />
          </div>
          <span className="text-lg font-semibold tracking-wider text-amber font-outfit">CHAINMIND</span>
        </Link>

        {/* Metric Cards */}
        <div className="flex items-center gap-3 flex-1">
          {cards.map((c) => (
            <div key={c.label} className="flex items-center gap-2 bg-bg/60 border border-white/5 rounded-lg px-3 py-1.5 min-w-[120px]">
              <c.icon className={`w-4 h-4 ${c.color}`} />
              <div>
                <div className="text-[10px] text-text/40 uppercase tracking-wider">{c.label}</div>
                <div className="flex items-center gap-1">
                  <span className="text-sm font-semibold text-text">{c.value}</span>
                  <span className={`text-[10px] ${c.change?.startsWith('+') ? 'text-amber' : 'text-green'}`}>{c.change}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Status indicators */}
        <div className="flex items-center gap-3 ml-4">
          <div className="flex items-center gap-1.5 bg-bg/60 border border-white/5 rounded-lg px-3 py-1.5">
            <Wifi className="w-3.5 h-3.5 text-green" />
            <span className="text-xs text-text/60">Ollama</span>
            <span className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
          </div>
          <div className="flex items-center gap-1.5 bg-bg/60 border border-white/5 rounded-lg px-3 py-1.5">
            <Cpu className="w-3.5 h-3.5 text-purple" />
            <span className="text-xs text-text/60">
              {metrics ? `${metrics.agentsActive}/${metrics.agentsTotal}` : '—'} agents
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
          </div>
        </div>
      </div>
    </nav>
  );
}
