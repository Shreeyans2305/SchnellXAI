import { useState } from 'react';
import { X, CheckCircle, XCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import { executeApproval, rejectApproval } from '../services/api';
import { useApproval } from '../context/ApprovalContext';

export default function ApprovalModal({ onClose }) {
  const { pendingApproval: approval, refresh } = useApproval();
  const [executing, setExecuting] = useState(false);

  if (!approval) return null;

  const handleApprove = async () => {
    setExecuting(true);
    await executeApproval(approval.id);
    refresh();
    onClose?.();
  };

  const handleReject = async () => {
    await rejectApproval(approval.id);
    refresh();
    onClose?.();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-sidebar/40 backdrop-blur-sm">
      <div className="bg-surface border border-border rounded-2xl w-full max-w-lg mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber" />
            <h2 className="text-base font-semibold text-text">Human Approval Required</h2>
          </div>
          <button onClick={onClose} className="text-muted hover:text-text transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          <div className="bg-amber/5 border border-amber/20 rounded-xl p-4">
            <div className="text-sm font-semibold text-amber">{approval.action}</div>
            <div className="text-xs text-muted mt-1 font-mono">{approval.shipmentId}</div>
          </div>

          {/* Routes */}
          <div className="grid grid-cols-2 gap-3">
            <div className="border border-border rounded-xl p-4 bg-bg">
              <div className="text-[10px] text-muted uppercase tracking-wider mb-2">Current Route</div>
              <div className="flex items-center gap-1 flex-wrap">
                {approval.currentRoute.map((r, i) => (
                  <span key={i} className="flex items-center gap-1">
                    <span className="text-xs text-red font-medium">{r}</span>
                    {i < approval.currentRoute.length - 1 && <ArrowRight className="w-3 h-3 text-muted" />}
                  </span>
                ))}
              </div>
            </div>
            <div className="border border-amber/20 rounded-xl p-4 bg-amber/5">
              <div className="text-[10px] text-amber uppercase tracking-wider mb-2">Proposed Route</div>
              <div className="flex items-center gap-1 flex-wrap">
                {approval.proposedRoute.map((r, i) => (
                  <span key={i} className="flex items-center gap-1">
                    <span className="text-xs text-green font-medium">{r}</span>
                    {i < approval.proposedRoute.length - 1 && <ArrowRight className="w-3 h-3 text-muted" />}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-4 gap-2">
            {[
              { label: 'Blast Radius', value: `${approval.blastRadius} shipments`, color: 'text-amber' },
              { label: 'Net Score', value: approval.netScore, color: 'text-green' },
              { label: 'Cost Delta', value: approval.costDelta, color: 'text-red' },
              { label: 'SLA Impact', value: approval.slaImpact, color: 'text-blue' },
            ].map((m) => (
              <div key={m.label} className="border border-border rounded-xl p-3 bg-bg text-center">
                <div className="text-[9px] text-muted uppercase">{m.label}</div>
                <div className={`text-sm font-semibold ${m.color} font-mono`}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Reasoning */}
          <div className="border border-border rounded-xl p-4 bg-bg">
            <div className="text-[10px] text-muted uppercase tracking-wider mb-1">Agent Reasoning</div>
            <p className="text-xs text-text/70 leading-relaxed">{approval.reason}</p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center gap-3 p-5 border-t border-border">
          <button
            onClick={handleReject}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border border-red/20 text-red text-sm hover:bg-red/5 transition-colors"
          >
            <XCircle className="w-4 h-4" />
            Reject
          </button>
          <button
            onClick={handleApprove}
            disabled={executing}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-amber text-white text-sm font-semibold hover:bg-amber/90 transition-colors disabled:opacity-50"
          >
            <CheckCircle className="w-4 h-4" />
            {executing ? 'Executing...' : 'Approve & Execute'}
          </button>
        </div>
      </div>
    </div>
  );
}
