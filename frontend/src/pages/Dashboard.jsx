import { useState } from 'react';
import AgentMesh from '../components/AgentMesh';
import ShipmentTable from '../components/ShipmentTable';
import CarrierCards from '../components/CarrierCards';
import ApprovalModal from '../components/ApprovalModal';
import { Bell } from 'lucide-react';

export default function Dashboard() {
  const [showApproval, setShowApproval] = useState(false);

  return (
    <div className="space-y-5 px-6 pb-6 overflow-y-auto h-full">
      {/* Approval Alert Banner */}
      <button
        onClick={() => setShowApproval(true)}
        className="w-full flex items-center gap-3 bg-amber/5 border border-amber/20 rounded-2xl p-4 hover:bg-amber/10 transition-colors text-left group shadow-card"
      >
        <div className="w-10 h-10 bg-amber/20 rounded-xl flex items-center justify-center shrink-0">
          <Bell className="w-5 h-5 text-amber" />
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-amber">Pending Approval — Decider Agent</div>
          <div className="text-xs text-muted mt-0.5">Reroute SHP-4821 via Pune Hub — requires manager authorization</div>
        </div>
        <span className="text-xs text-amber border border-amber/30 px-3 py-1.5 rounded-xl font-medium group-hover:bg-amber group-hover:text-white transition-colors">
          Review
        </span>
      </button>

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

      {/* Approval Modal */}
      {showApproval && <ApprovalModal onClose={() => setShowApproval(false)} />}
    </div>
  );
}

function AgentActivityStream() {
  const activities = [
    { time: '10:18:30', agent: 'Reasoner', color: '#8b5cf6', action: 'Cluster analysis: 3 shipments can consolidate at Pune Hub' },
    { time: '10:17:55', agent: 'Observer', color: '#3b82f6', action: 'SHP-5567 temperature excursion detected — cold chain at risk' },
    { time: '10:17:12', agent: 'Executor', color: '#42d65c', action: 'SHP-3192 new manifest dispatched to Delhivery' },
    { time: '10:16:45', agent: 'Decider', color: '#f5a623', action: 'SHP-4821 reroute requires manager approval — cost delta +₹2,400' },
    { time: '10:16:02', agent: 'Learner', color: '#b32826', action: 'Route pattern Nagpur→Mumbai via Pune 12% faster historically' },
    { time: '10:15:18', agent: 'Observer', color: '#3b82f6', action: 'SHP-7734 carrier delay detected — BlueDart Nagpur' },
    { time: '10:15:01', agent: 'Executor', color: '#42d65c', action: 'SHP-3192 rerouted via Pune Hub — ETA adjusted +2h' },
    { time: '10:14:32', agent: 'Observer', color: '#3b82f6', action: 'SHP-4821 Nagpur hub throughput drop −34%' },
  ];

  return (
    <div className="bg-surface border border-border rounded-2xl p-5 h-full shadow-card">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
        <h3 className="text-sm font-semibold text-text">Agent Activity Stream</h3>
        <span className="text-[10px] text-muted ml-auto font-mono bg-bg px-2 py-0.5 rounded-lg">LIVE FEED</span>
      </div>
      <div className="space-y-1 max-h-[340px] overflow-y-auto pr-1">
        {activities.map((a, i) => (
          <div key={i} className="flex items-start gap-3 py-2 border-b border-border/50 last:border-0">
            <span className="text-[10px] text-muted font-mono shrink-0 pt-0.5">{a.time}</span>
            <span
              className="text-[10px] font-semibold shrink-0 px-2 py-0.5 rounded-lg"
              style={{ color: a.color, backgroundColor: `${a.color}15` }}
            >
              {a.agent}
            </span>
            <span className="text-xs text-muted leading-relaxed">{a.action}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
