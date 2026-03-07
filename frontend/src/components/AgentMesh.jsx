import { useAgents } from '../hooks/useAgents';
import { Activity } from 'lucide-react';
import { useEffect, useState } from 'react';

const agentPositions = {
  observer: { x: 200, y: 40 },
  reasoner: { x: 80, y: 140 },
  decider: { x: 320, y: 140 },
  executor: { x: 200, y: 240 },
  learner: { x: 200, y: 330 },
};

export default function AgentMesh() {
  const { agents, edges, loading } = useAgents();
  const [activeEdges, setActiveEdges] = useState(new Set());

  useEffect(() => {
    const interval = setInterval(() => {
      const nextActive = new Set();
      edges.forEach((e, i) => {
        if (Math.random() > 0.4) nextActive.add(i);
      });
      setActiveEdges(nextActive);
    }, 2000);
    return () => clearInterval(interval);
  }, [edges]);

  if (loading) {
    return (
      <div className="bg-surface border border-amber/10 rounded-xl p-4 h-full flex items-center justify-center">
        <Activity className="w-6 h-6 text-amber animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-surface border border-amber/10 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Activity className="w-4 h-4 text-amber" />
        <h3 className="text-sm font-semibold text-text">Agent Mesh Network</h3>
        <span className="text-[10px] text-text/30 ml-auto font-mono">LIVE</span>
        <span className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
      </div>

      <svg viewBox="0 0 400 380" className="w-full">
        {/* Edges */}
        {edges.map((edge, i) => {
          const from = agentPositions[edge.from];
          const to = agentPositions[edge.to];
          if (!from || !to) return null;
          const isActive = activeEdges.has(i);
          return (
            <line
              key={i}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={isActive ? '#f5a623' : '#2a2722'}
              strokeWidth={isActive ? 2 : 1}
              strokeDasharray={isActive ? '6 3' : '4 4'}
              className={isActive ? 'animate-flow' : ''}
              opacity={isActive ? 1 : 0.4}
            />
          );
        })}

        {/* Agent Nodes */}
        {agents.map((agent) => {
          const pos = agentPositions[agent.id];
          if (!pos) return null;
          return (
            <g key={agent.id}>
              {/* Glow */}
              <circle cx={pos.x} cy={pos.y} r="28" fill={agent.color} opacity="0.08" />
              <circle cx={pos.x} cy={pos.y} r="22" fill="#161512" stroke={agent.color} strokeWidth="1.5" />
              {/* Label */}
              <text x={pos.x} y={pos.y - 2} textAnchor="middle" fill={agent.color} fontSize="9" fontWeight="600" fontFamily="Outfit">
                {agent.name.toUpperCase()}
              </text>
              <text x={pos.x} y={pos.y + 10} textAnchor="middle" fill="#e8dcc8" fontSize="7" opacity="0.4" fontFamily="JetBrains Mono">
                {agent.load}% load
              </text>
            </g>
          );
        })}
      </svg>

      {/* Agent status list */}
      <div className="grid grid-cols-5 gap-1 mt-2">
        {agents.map((a) => (
          <div key={a.id} className="text-center">
            <div className="w-2 h-2 rounded-full mx-auto mb-0.5" style={{ backgroundColor: a.color }} />
            <div className="text-[9px] text-text/40 font-mono truncate">{a.messagesProcessed}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
