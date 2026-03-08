import { useState, useEffect } from 'react';
import AgentMesh from '../components/AgentMesh';
import ShipmentTable from '../components/ShipmentTable';
import CarrierCards from '../components/CarrierCards';
import { Bell, AlertTriangle, RotateCcw, GraduationCap, CheckCircle2, Zap, Lightbulb } from 'lucide-react';
import { getEvents } from '../services/api';
import { useApproval } from '../context/ApprovalContext';

export default function Dashboard() {
  const { pendingApproval, setShowModal } = useApproval();

  return (
    <div className="space-y-5 px-6 pb-6 overflow-y-auto h-full">

      {/* Approval Banner — scrolls with content */}
      {pendingApproval ? (
        <button
          onClick={() => setShowModal(true)}
          className="w-full flex items-center gap-3 bg-amber/5 border border-amber/20 rounded-2xl p-4 hover:bg-amber/10 transition-colors text-left group shadow-card"
        >
          <div className="w-10 h-10 bg-amber/20 rounded-xl flex items-center justify-center shrink-0">
            <Bell className="w-5 h-5 text-amber animate-pulse" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-amber">
              Pending Approval — {pendingApproval.shipmentId || pendingApproval.shipment_id || 'Shipment'}
            </div>
            <div className="text-xs text-muted mt-0.5 truncate">
              {pendingApproval.action || 'Action requires human authorization'}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs text-amber border border-amber/30 px-3 py-1.5 rounded-xl font-medium group-hover:bg-amber group-hover:text-white transition-colors">
              Review
            </span>
          </div>
        </button>
      ) : (
        <div className="w-full flex items-center gap-3 bg-green/5 border border-green/20 rounded-2xl p-4 shadow-card">
          <div className="w-10 h-10 bg-green/20 rounded-xl flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-5 h-5 text-green" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-green">No Actions Need Approval</div>
            <div className="text-xs text-muted mt-0.5">All agent decisions are within autonomous thresholds</div>
          </div>
        </div>
      )}

      {/* Agent Mesh + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-1">
          <AgentMesh />
        </div>
        <div className="lg:col-span-2">
          <AgentActivityStream />
        </div>
      </div>

      {/* Shipments */}
      <ShipmentTable />

      {/* Carriers */}
      <CarrierCards />
    </div>
  );
}

function AgentActivityStream() {
  const [activities, setActivities] = useState([]);
  const [activeTab, setActiveTab] = useState('ALL');

  useEffect(() => {
    getEvents().then((data) => {
      if (Array.isArray(data)) setActivities(data);
    });
    const id = setInterval(() => {
      getEvents().then((data) => {
        if (Array.isArray(data)) setActivities(data);
      });
    }, 5000);
    return () => clearInterval(id);
  }, []);

  const categories = [
    { key: 'ALL',      label: 'All',         icon: Zap,            color: '#6b7280', bg: 'bg-muted/10' },
    { key: 'ANOMALY',  label: 'Anomalies',   icon: AlertTriangle,  color: '#b32826', bg: 'bg-red/10' },
    { key: 'OPTIMIZE', label: 'Optimize',    icon: Lightbulb,      color: '#8b5cf6', bg: 'bg-purple/10' },
    { key: 'REROUTE',  label: 'Reroutes',    icon: RotateCcw,      color: '#f5a623', bg: 'bg-amber/10' },
    { key: 'EXECUTE',  label: 'Executions',  icon: CheckCircle2,   color: '#42d65c', bg: 'bg-green/10' },
    { key: 'APPROVAL', label: 'Approvals',   icon: Bell,           color: '#f5a623', bg: 'bg-amber/10' },
    { key: 'LEARNING', label: 'Learning',    icon: GraduationCap,  color: '#3b82f6', bg: 'bg-blue/10' },
  ];

  const filtered = activeTab === 'ALL' ? activities : activities.filter((a) => a.type === activeTab);

  const counts = {};
  for (const a of activities) {
    counts[a.type] = (counts[a.type] || 0) + 1;
  }

  const activeCat = categories.find((c) => c.key === activeTab) || categories[0];

  return (
    <div className="bg-surface border border-border rounded-2xl p-5 h-full shadow-card flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-2 h-2 rounded-full ${activities.length > 0 ? 'bg-green animate-pulse' : 'bg-muted'}`} />
        <h3 className="text-sm font-semibold text-text">Agent Activity Stream</h3>
        <span className="text-[10px] text-muted ml-auto font-mono bg-bg px-2 py-0.5 rounded-lg">{activities.length > 0 ? `${activities.length} EVENTS` : 'WAITING'}</span>
      </div>

      {/* Category tabs */}
      <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1">
        {categories.map((cat) => {
          const count = cat.key === 'ALL' ? activities.length : (counts[cat.key] || 0);
          const isActive = activeTab === cat.key;
          const Icon = cat.icon;
          return (
            <button
              key={cat.key}
              onClick={() => setActiveTab(cat.key)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-[11px] font-medium whitespace-nowrap transition-all border ${
                isActive
                  ? 'border-current shadow-sm'
                  : 'border-transparent hover:bg-bg'
              }`}
              style={isActive ? { color: cat.color, backgroundColor: `${cat.color}10` } : { color: '#6b7280' }}
            >
              <Icon className="w-3 h-3" />
              {cat.label}
              {count > 0 && (
                <span
                  className="text-[9px] font-bold rounded-md px-1.5 py-0.5 leading-none"
                  style={isActive ? { backgroundColor: `${cat.color}20`, color: cat.color } : { backgroundColor: '#f0f1f5', color: '#6b7280' }}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Event list */}
      {activities.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 text-center py-8">
          <div className="w-12 h-12 rounded-2xl bg-bg border border-border flex items-center justify-center mb-3">
            <Bell className="w-5 h-5 text-muted/40" />
          </div>
          <p className="text-xs text-muted">No agent activity yet</p>
          <p className="text-[10px] text-muted/60 mt-1">Run a simulation or generate disruptions to see agent events</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 text-center py-8">
          <activeCat.icon className="w-6 h-6 mb-2" style={{ color: `${activeCat.color}50` }} />
          <p className="text-xs text-muted">No {activeCat.label.toLowerCase()} events</p>
        </div>
      ) : (
        <div className="space-y-1 flex-1 overflow-y-auto pr-1 max-h-[320px]">
          {filtered.map((a, i) => {
            const cat = categories.find((c) => c.key === a.type) || categories[0];
            const Icon = cat.icon;
            return (
              <div key={i} className="flex items-start gap-2.5 py-2 border-b border-border/50 last:border-0">
                <div
                  className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                  style={{ backgroundColor: `${cat.color}12` }}
                >
                  <Icon className="w-3 h-3" style={{ color: cat.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span
                      className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md"
                      style={{ color: cat.color, backgroundColor: `${cat.color}15` }}
                    >
                      {a.type}
                    </span>
                    <span className="text-[10px] text-muted/60 font-mono">{a.flow}</span>
                    <span className="text-[10px] text-muted font-mono ml-auto shrink-0">{a.time}</span>
                  </div>
                  <p className="text-xs text-text/70 leading-relaxed truncate">{a.message}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
