import { useState, useEffect } from 'react';
import AgentMesh from '../components/AgentMesh';
import ShipmentTable from '../components/ShipmentTable';
import CarrierCards from '../components/CarrierCards';
import ApprovalModal from '../components/ApprovalModal';
import { Bell } from 'lucide-react';
import { getEvents, getApproval } from '../services/api';

export default function Dashboard() {
  const [showApproval, setShowApproval] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(null);

  useEffect(() => {
    getApproval().then((data) => {
      if (data && data.id) setPendingApproval(data);
      else setPendingApproval(null);
    });
    const id = setInterval(() => {
      getApproval().then((data) => {
        if (data && data.id) setPendingApproval(data);
        else setPendingApproval(null);
      });
    }, 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-5 px-6 pb-6 overflow-y-auto h-full">
      {/* Approval Alert Banner — only shown when there's a pending approval */}
      {pendingApproval ? (
        <button
          onClick={() => setShowApproval(true)}
          className="w-full flex items-center gap-3 bg-amber/5 border border-amber/20 rounded-2xl p-4 hover:bg-amber/10 transition-colors text-left group shadow-card"
        >
          <div className="w-10 h-10 bg-amber/20 rounded-xl flex items-center justify-center shrink-0">
            <Bell className="w-5 h-5 text-amber" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-semibold text-amber">Pending Approval — Decider Agent</div>
            <div className="text-xs text-muted mt-0.5">{pendingApproval.action || 'Action requires authorization'}</div>
          </div>
          <span className="text-xs text-amber border border-amber/30 px-3 py-1.5 rounded-xl font-medium group-hover:bg-amber group-hover:text-white transition-colors">
            Review
          </span>
        </button>
      ) : (
        <div className="w-full flex items-center gap-3 bg-bg border border-border rounded-2xl p-4 shadow-card">
          <div className="w-10 h-10 bg-green/10 rounded-xl flex items-center justify-center shrink-0">
            <Bell className="w-5 h-5 text-green/50" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium text-muted">No pending approvals</div>
            <div className="text-xs text-muted/60 mt-0.5">All agent actions are either auto-approved or awaiting simulation</div>
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

      {/* Approval Modal */}
      {showApproval && <ApprovalModal onClose={() => setShowApproval(false)} />}
    </div>
  );
}

function AgentActivityStream() {
  const [activities, setActivities] = useState([]);

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

  const agentColorMap = {
    observer: '#3b82f6',
    reasoner: '#8b5cf6',
    decider: '#f5a623',
    executor: '#42d65c',
    learner: '#b32826',
  };

  return (
    <div className="bg-surface border border-border rounded-2xl p-5 h-full shadow-card">
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-2 h-2 rounded-full ${activities.length > 0 ? 'bg-green animate-pulse' : 'bg-muted'}`} />
        <h3 className="text-sm font-semibold text-text">Agent Activity Stream</h3>
        <span className="text-[10px] text-muted ml-auto font-mono bg-bg px-2 py-0.5 rounded-lg">{activities.length > 0 ? 'LIVE FEED' : 'WAITING'}</span>
      </div>
      {activities.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[300px] text-center">
          <div className="w-12 h-12 rounded-2xl bg-bg border border-border flex items-center justify-center mb-3">
            <Bell className="w-5 h-5 text-muted/40" />
          </div>
          <p className="text-xs text-muted">No agent activity yet</p>
          <p className="text-[10px] text-muted/60 mt-1">Run a simulation or generate disruptions to see agent events</p>
        </div>
      ) : (
        <div className="space-y-1 max-h-[340px] overflow-y-auto pr-1">
          {activities.map((a, i) => {
            const agentName = (a.flow || '').split(' \u2192 ')[0].trim().toLowerCase();
            const color = agentColorMap[agentName] || '#6b7280';
            return (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-border/50 last:border-0">
                <span className="text-[10px] text-muted font-mono shrink-0 pt-0.5">{a.time}</span>
                <span
                  className="text-[10px] font-semibold shrink-0 px-2 py-0.5 rounded-lg"
                  style={{ color, backgroundColor: `${color}15` }}
                >
                  {a.type}
                </span>
                <span className="text-xs text-muted leading-relaxed">{a.message}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
