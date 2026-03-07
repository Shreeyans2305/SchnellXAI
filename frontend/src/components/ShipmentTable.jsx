import { useShipments } from '../hooks/useShipments';
import { Truck, AlertTriangle, Clock, CheckCircle } from 'lucide-react';

const statusConfig = {
  'ON TRACK': { bg: 'bg-green/10', text: 'text-green', border: 'border-green/20', icon: CheckCircle },
  'AT RISK': { bg: 'bg-amber/10', text: 'text-amber', border: 'border-amber/20', icon: AlertTriangle },
  'DELAYED': { bg: 'bg-red/10', text: 'text-red', border: 'border-red/20', icon: Clock },
};

function RiskBar({ value }) {
  const color = value > 70 ? 'bg-red' : value > 40 ? 'bg-amber' : 'bg-green';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-border/50 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-[10px] text-muted font-mono w-6">{value}%</span>
    </div>
  );
}

function ProgressBar({ value }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-border/50 rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-blue" style={{ width: `${value}%` }} />
      </div>
      <span className="text-[10px] text-muted font-mono w-6">{value}%</span>
    </div>
  );
}

export default function ShipmentTable() {
  const { shipments, loading } = useShipments();

  return (
    <div className="bg-surface border border-border rounded-2xl p-5 shadow-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Truck className="w-4 h-4 text-amber" />
          <h3 className="text-sm font-semibold text-text">Active Shipments</h3>
          <span className="text-[10px] text-muted px-2 py-0.5 bg-bg rounded-lg font-mono">
            {shipments.length}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border">
              {['ID', 'Route', 'Carrier', 'Progress', 'ETA', 'SLA', 'Risk', 'Agent', 'Status', 'Notes'].map((h) => (
                <th key={h} className="text-left text-[10px] text-muted uppercase tracking-wider py-3 px-2 font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} className="text-center py-8 text-muted">Loading shipments...</td>
              </tr>
            ) : shipments.length === 0 ? (
              <tr>
                <td colSpan={10} className="text-center py-12">
                  <div className="flex flex-col items-center gap-2">
                    <Truck className="w-8 h-8 text-muted/30" />
                    <p className="text-xs text-muted">No active shipments</p>
                    <p className="text-[10px] text-muted/60">Go to Simulation → Generate Sample System to create test data</p>
                  </div>
                </td>
              </tr>
            ) : (
              shipments.map((s) => {
                const cfg = statusConfig[s.status] || statusConfig['ON TRACK'];
                return (
                  <tr key={s.id} className="border-b border-border/50 hover:bg-bg/50 transition-colors">
                    <td className="py-3 px-2 font-mono text-amber font-medium">{s.id}</td>
                    <td className="py-3 px-2 text-text/80">{s.route}</td>
                    <td className="py-3 px-2 text-muted">{s.carrier}</td>
                    <td className="py-3 px-2"><ProgressBar value={s.progress} /></td>
                    <td className="py-3 px-2 font-mono text-muted">{s.eta}</td>
                    <td className="py-3 px-2">
                      <span className="text-[10px] px-2 py-0.5 bg-bg rounded-lg text-muted">{s.sla}</span>
                    </td>
                    <td className="py-3 px-2"><RiskBar value={s.risk} /></td>
                    <td className="py-3 px-2 text-purple text-[10px] font-mono font-medium">{s.agent}</td>
                    <td className="py-3 px-2">
                      <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
                        <cfg.icon className="w-2.5 h-2.5" />
                        {s.status}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-muted max-w-[200px] truncate">{s.notes}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
