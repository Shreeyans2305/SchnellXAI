import { useState } from 'react';
import { FlaskConical, CheckCircle, AlertTriangle, DollarSign, Clock, Zap, Brain } from 'lucide-react';
import { runSimulation, mockSimulationResult } from '../services/api';

export default function SimulationPanel() {
  const [result, setResult] = useState(mockSimulationResult);
  const [running, setRunning] = useState(false);
  const [selected, setSelected] = useState(null);

  const handleRun = async () => {
    setRunning(true);
    try {
      const res = await runSimulation({ shipmentId: 'SHP-4821', hub: 'Nagpur' });
      setResult(res.data || mockSimulationResult);
    } catch {
      setResult(mockSimulationResult);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Simulation Controls */}
      <div className="bg-surface border border-amber/10 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-amber" />
            <h3 className="text-sm font-semibold text-text">Route Simulation Engine</h3>
          </div>
          <button
            onClick={handleRun}
            disabled={running}
            className="flex items-center gap-2 px-4 py-2 bg-amber text-bg text-xs font-semibold rounded-lg hover:bg-amber/90 transition-colors disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5" />
            {running ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {result.options.map((opt) => (
            <button
              key={opt.id}
              onClick={() => setSelected(opt.id)}
              className={`text-left border rounded-lg p-3 transition-all ${
                selected === opt.id
                  ? 'border-amber/40 bg-amber/5'
                  : opt.recommended
                  ? 'border-green/20 bg-green/5'
                  : 'border-white/5 bg-bg/40'
              } hover:border-amber/30`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-text">{opt.name}</span>
                {opt.recommended && (
                  <span className="text-[9px] text-green bg-green/10 px-1.5 py-0.5 rounded-full border border-green/20">
                    RECOMMENDED
                  </span>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <div className="text-[9px] text-text/30 uppercase">Net Score</div>
                  <div className={`text-lg font-bold font-mono ${opt.netScore >= 70 ? 'text-green' : opt.netScore >= 50 ? 'text-amber' : 'text-red'}`}>
                    {opt.netScore}
                  </div>
                </div>
                <div>
                  <div className="text-[9px] text-text/30 uppercase">Blast Radius</div>
                  <div className="text-lg font-bold text-amber font-mono">{opt.blastRadius}</div>
                </div>
                <div>
                  <div className="text-[9px] text-text/30 uppercase">SLA Impact</div>
                  <div className="text-xs text-text/60 font-mono">{opt.slaImpact}</div>
                </div>
                <div>
                  <div className="text-[9px] text-text/30 uppercase">Cost</div>
                  <div className="text-xs text-text/60 font-mono">{opt.cost}</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Cascade Impact */}
      <div className="bg-surface border border-amber/10 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="w-4 h-4 text-amber" />
          <h3 className="text-sm font-semibold text-text">Cascade Impact Analysis</h3>
        </div>
        <div className="space-y-2">
          {result.cascadeImpact.map((c, i) => {
            const sevColor = c.severity === 'high' ? 'border-red/20 bg-red/5' : c.severity === 'medium' ? 'border-amber/20 bg-amber/5' : 'border-white/5 bg-bg/40';
            return (
              <div key={i} className={`border rounded-lg p-3 ${sevColor} flex items-center justify-between`}>
                <div>
                  <span className="text-xs font-mono text-amber">{c.shipment}</span>
                  <span className="text-xs text-text/50 ml-2">{c.impact}</span>
                </div>
                <span className={`text-[9px] uppercase px-2 py-0.5 rounded-full ${
                  c.severity === 'high' ? 'text-red bg-red/10' : c.severity === 'medium' ? 'text-amber bg-amber/10' : 'text-text/40 bg-white/5'
                }`}>
                  {c.severity}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Agent Reasoning */}
      <div className="bg-surface border border-amber/10 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="w-4 h-4 text-purple" />
          <h3 className="text-sm font-semibold text-text">Agent Reasoning Chain</h3>
        </div>
        <div className="border border-white/5 rounded-lg p-4 bg-bg/40">
          <p className="text-xs text-text/60 leading-relaxed font-mono">{result.reasoning}</p>
        </div>
        <div className="flex items-center gap-3 mt-3">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue" />
            <span className="text-[9px] text-text/30">Observer</span>
          </div>
          <span className="text-text/10">→</span>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple" />
            <span className="text-[9px] text-text/30">Reasoner</span>
          </div>
          <span className="text-text/10">→</span>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber" />
            <span className="text-[9px] text-text/30">Decider</span>
          </div>
        </div>
      </div>
    </div>
  );
}
