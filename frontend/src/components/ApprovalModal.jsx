import { useState } from 'react';
import { X, CheckCircle, XCircle, AlertTriangle, ArrowRight, MapPin, Truck } from 'lucide-react';
import { executeApproval, rejectApproval } from '../services/api';
import { useApproval } from '../context/ApprovalContext';

export default function ApprovalModal({ onClose }) {
  const { pendingApproval: approval, refresh } = useApproval();
  const [executing, setExecuting] = useState(false);

  if (!approval) return null;

  // Backend returns snake_case; support both formats
  const currentRoute = approval.currentRoute || approval.current_route || [];
  const proposedRoute = approval.proposedRoute || approval.proposed_route || [];
  const blastRadius = approval.blastRadius ?? approval.blast_radius ?? '—';
  const netScore = approval.netScore ?? approval.net_score ?? '—';
  const slaImpact = approval.slaImpact || approval.sla_impact || '—';
  const reason = approval.reason || approval.rationale || 'No reasoning provided.';
  const shipmentId = approval.shipmentId || approval.shipment_id || '';
  const actionType = approval.action_type || approval.actionType || 'action';
  const isHubReroute = actionType === 'temporary_hub_reroute';
  const targetHub = approval.target_hub || approval.targetHub || '';
  const affectedShipments = approval.affected_shipments || approval.affectedShipments || [];
  const bypassHubs = approval.bypass_hubs || approval.bypassHubs || proposedRoute;
  const riskScore = approval.risk_score ?? approval.riskScore ?? null;

  const handleApprove = async () => {
    setExecuting(true);
    try {
      await executeApproval(approval.id);
      await refresh();
      onClose?.();
    } catch {
      setExecuting(false);
    }
  };

  const handleReject = async () => {
    setExecuting(true);
    try {
      await rejectApproval(approval.id);
      await refresh();
      onClose?.();
    } catch {
      setExecuting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-sidebar/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-surface border border-border rounded-2xl w-full max-w-lg mx-4 shadow-2xl animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border sticky top-0 bg-surface z-10 rounded-t-2xl">
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
          {/* Action summary */}
          <div className="bg-amber/5 border border-amber/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="text-[10px] font-bold uppercase tracking-wider bg-amber/20 text-amber px-2 py-0.5 rounded">
                {actionType.replace(/_/g, ' ')}
              </span>
              {riskScore != null && riskScore > 0 && (
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                  riskScore >= 80 ? 'bg-red/10 text-red' : riskScore >= 50 ? 'bg-amber/10 text-amber' : 'bg-green/10 text-green'
                }`}>
                  Risk {riskScore}%
                </span>
              )}
            </div>
            <div className="text-sm font-semibold text-text">{approval.action || 'Proposed action'}</div>
            {isHubReroute && targetHub ? (
              <div className="flex items-center gap-1.5 mt-1.5">
                <MapPin className="w-3 h-3 text-red" />
                <span className="text-xs text-red font-medium">{targetHub}</span>
                <span className="text-[10px] text-muted">— congested</span>
              </div>
            ) : (
              shipmentId && <div className="text-xs text-muted mt-1 font-mono">{shipmentId}</div>
            )}
          </div>

          {/* Affected shipments list (for hub-level reroutes) */}
          {isHubReroute && affectedShipments.length > 0 && (
            <div className="border border-red/15 rounded-xl p-4 bg-red/3">
              <div className="text-[10px] text-red uppercase tracking-wider mb-2 font-semibold">Affected Shipments ({affectedShipments.length})</div>
              <div className="flex flex-wrap gap-1.5">
                {affectedShipments.map((sid) => (
                  <span key={sid} className="inline-flex items-center gap-1 text-[11px] font-mono bg-surface border border-border px-2 py-1 rounded-lg">
                    <Truck className="w-3 h-3 text-muted" />
                    {sid}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Routes / Bypass */}
          {isHubReroute ? (
            <>
              {/* Congested hub + bypass summary */}
              {(targetHub || bypassHubs.length > 0) && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="border border-red/20 rounded-xl p-4 bg-red/3">
                    <div className="text-[10px] text-red uppercase tracking-wider mb-2 font-semibold">Congested Hub</div>
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-red" />
                      <span className="text-xs text-red font-semibold">{targetHub || 'Hub'}</span>
                    </div>
                  </div>
                  <div className="border border-green/20 rounded-xl p-4 bg-green/3">
                    <div className="text-[10px] text-green uppercase tracking-wider mb-2 font-semibold">Bypass Via</div>
                    <div className="flex flex-col gap-1">
                      {bypassHubs.map((h, i) => (
                        <div key={i} className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-green" />
                          <span className="text-xs text-green font-semibold">{h}</span>
                        </div>
                      ))}
                      {bypassHubs.length === 0 && proposedRoute.length > 0 && proposedRoute.map((h, i) => (
                        <div key={i} className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-green" />
                          <span className="text-xs text-green font-semibold">{h}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Per-shipment current → proposed routes */}
              {approval.per_shipment_routes && Object.keys(approval.per_shipment_routes).length > 0 && (
                <div className="border border-border rounded-xl p-4 bg-bg">
                  <div className="text-[10px] text-muted uppercase tracking-wider mb-3 font-semibold">Reroute Plan per Shipment</div>
                  <div className="space-y-2.5">
                    {Object.entries(approval.per_shipment_routes).map(([sid, route]) => {
                      const curRoutes = approval.current_routes_by_ship || {};
                      const curRoute = curRoutes[sid] || [];
                      return (
                        <div key={sid} className="border border-border/50 rounded-lg p-2.5 bg-surface">
                          <div className="flex items-center gap-1.5 mb-1.5">
                            <Truck className="w-3 h-3 text-muted" />
                            <span className="font-mono text-[11px] text-text font-semibold">{sid}</span>
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <div className="text-[9px] text-red/70 uppercase mb-1">Current</div>
                              <div className="flex items-center gap-1 flex-wrap">
                                {curRoute.length > 0 ? curRoute.map((hop, i) => (
                                  <span key={i} className="flex items-center gap-0.5">
                                    <span className="text-[11px] text-red/80 font-medium">{hop}</span>
                                    {i < curRoute.length - 1 && <ArrowRight className="w-2.5 h-2.5 text-muted/50" />}
                                  </span>
                                )) : (
                                  <span className="text-[11px] text-muted italic">via {targetHub || 'congested hub'}</span>
                                )}
                              </div>
                            </div>
                            <div>
                              <div className="text-[9px] text-green/70 uppercase mb-1">Proposed</div>
                              <div className="flex items-center gap-1 flex-wrap">
                                {route.map((hop, i) => (
                                  <span key={i} className="flex items-center gap-0.5">
                                    <span className="text-[11px] text-green font-medium">{hop}</span>
                                    {i < route.length - 1 && <ArrowRight className="w-2.5 h-2.5 text-muted/50" />}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          ) : (currentRoute.length > 0 || proposedRoute.length > 0) ? (
            <div className="grid grid-cols-2 gap-3">
              <div className="border border-border rounded-xl p-4 bg-bg">
                <div className="text-[10px] text-muted uppercase tracking-wider mb-2">Current Route</div>
                <div className="flex items-center gap-1 flex-wrap">
                  {currentRoute.map((r, i) => (
                    <span key={i} className="flex items-center gap-1">
                      <span className="text-xs text-red font-medium">{r}</span>
                      {i < currentRoute.length - 1 && <ArrowRight className="w-3 h-3 text-muted" />}
                    </span>
                  ))}
                </div>
              </div>
              <div className="border border-amber/20 rounded-xl p-4 bg-amber/5">
                <div className="text-[10px] text-amber uppercase tracking-wider mb-2">Proposed Route</div>
                <div className="flex items-center gap-1 flex-wrap">
                  {proposedRoute.map((r, i) => (
                    <span key={i} className="flex items-center gap-1">
                      <span className="text-xs text-green font-medium">{r}</span>
                      {i < proposedRoute.length - 1 && <ArrowRight className="w-3 h-3 text-muted" />}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : null}

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'Blast Radius', value: typeof blastRadius === 'number' ? `${blastRadius} shipments` : blastRadius, color: 'text-amber' },
              { label: 'Net Score', value: netScore, color: 'text-green' },
              { label: 'SLA Impact', value: slaImpact, color: 'text-blue' },
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
            <p className="text-xs text-text/70 leading-relaxed">{reason}</p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center gap-3 p-5 border-t border-border sticky bottom-0 bg-surface rounded-b-2xl">
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
