import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, Clock, Cpu, CheckCircle, Wifi, Search, Calendar } from 'lucide-react';
import { getMetrics } from '../services/api';

export default function Navbar() {
  const [metrics, setMetrics] = useState(null);
  const [period, setPeriod] = useState('Month');

  useEffect(() => {
    getMetrics().then(setMetrics);
    const id = setInterval(() => getMetrics().then(setMetrics), 15000);
    return () => clearInterval(id);
  }, []);

  const cards = metrics
    ? [
        { label: 'Shipments', value: metrics.shipments.value, change: metrics.shipments.change, icon: Activity, gradient: 'card-gradient-blue' },
        { label: 'At Risk', value: metrics.atRisk.value, change: metrics.atRisk.change, icon: AlertTriangle, gradient: 'card-gradient-orange' },
        { label: 'Delayed', value: metrics.delayed.value, change: metrics.delayed.change, icon: Clock, gradient: 'card-gradient-red' },
        { label: 'Agent Ops', value: typeof metrics.agentOps.value === 'number' ? metrics.agentOps.value.toLocaleString() : '0', change: metrics.agentOps.change, icon: Cpu, gradient: 'card-gradient-purple' },
        { label: 'Approvals', value: metrics.approvals.value, change: metrics.approvals.change, icon: CheckCircle, gradient: 'card-gradient-green' },
      ]
    : [
        { label: 'Shipments', value: 0, change: '—', icon: Activity, gradient: 'card-gradient-blue' },
        { label: 'At Risk', value: 0, change: '—', icon: AlertTriangle, gradient: 'card-gradient-orange' },
        { label: 'Delayed', value: 0, change: '—', icon: Clock, gradient: 'card-gradient-red' },
        { label: 'Agent Ops', value: 0, change: '—', icon: Cpu, gradient: 'card-gradient-purple' },
        { label: 'Approvals', value: 0, change: '—', icon: CheckCircle, gradient: 'card-gradient-green' },
      ];

  return (
    <nav className="w-full px-6 py-4">
      <div className="flex items-center justify-between mb-6">
        {/* Title Area */}
        <div>
          <h1 className="text-2xl font-bold text-text">Monitor health of your logistics</h1>
          <p className="text-sm text-muted mt-0.5">Control and analyze your data in the easiest way</p>
        </div>

        {/* Search + Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-surface border border-border rounded-xl px-4 py-2.5 shadow-card">
            <Search className="w-4 h-4 text-muted" />
            <input
              type="text"
              placeholder="Search"
              className="bg-transparent outline-none text-sm text-text placeholder:text-muted w-40"
            />
          </div>
          <button className="w-10 h-10 bg-surface border border-border rounded-xl flex items-center justify-center shadow-card hover:shadow-card-hover transition-shadow">
            <Calendar className="w-4 h-4 text-muted" />
          </button>

          {/* Period Toggle */}
          <div className="flex items-center bg-surface border border-border rounded-xl shadow-card overflow-hidden">
            {['Week', 'Month', 'Year'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 text-xs font-medium transition-all ${
                  period === p
                    ? 'bg-sidebar text-white'
                    : 'text-muted hover:text-text'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Status indicators */}
          <div className="flex items-center gap-1.5 bg-surface border border-border rounded-xl px-3 py-2 shadow-card">
            <Wifi className="w-3.5 h-3.5 text-green" />
            <span className="text-xs text-muted">Ollama</span>
            <span className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-5 gap-4">
        {cards.map((c) => (
          <div key={c.label} className={`${c.gradient} rounded-2xl p-4 shadow-card hover:shadow-card-hover transition-shadow`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-text/70">{c.label}</span>
              <c.icon className="w-4 h-4 text-text/40" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-bold text-text">{c.value}</span>
              <span className="text-xs font-medium mb-1 text-muted">
                {c.change}
              </span>
            </div>
          </div>
        ))}
      </div>
    </nav>
  );
}
