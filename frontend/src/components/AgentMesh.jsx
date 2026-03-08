import { useAgents } from '../hooks/useAgents';
import { Activity } from 'lucide-react';
import { useMemo } from 'react';

const agentPositions = {
  observer: { x: 200, y: 45 },
  reasoner: { x: 70,  y: 155 },
  decider:  { x: 330, y: 155 },
  executor: { x: 200, y: 255 },
  learner:  { x: 200, y: 345 },
  human:    { x: 380, y: 50 },
};

const AGENT_ICONS = {
  observer: '👁',
  reasoner: '🧠',
  decider:  '⚖️',
  executor: '⚡',
  learner:  '📚',
  human:    '👤',
};

export default function AgentMesh() {
  const { agents, edges, loading, extra } = useAgents();
  const currentAgent = extra?.currentAgent || '';

  const totalMessages = useMemo(() => agents.reduce((s, a) => s + (a.messagesProcessed || 0), 0), [agents]);
  const activeCount = useMemo(() => agents.filter((a) => a.status === 'active').length, [agents]);

  if (loading) {
    return (
      <div className="bg-surface border border-border rounded-2xl p-5 h-full flex items-center justify-center shadow-card">
        <Activity className="w-6 h-6 text-amber animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-2xl p-5 shadow-card">
      <div className="flex items-center gap-2 mb-2">
        <Activity className="w-4 h-4 text-amber" />
        <h3 className="text-sm font-semibold text-text">Agent Mesh Network</h3>
        <span className="text-[10px] text-muted ml-auto font-mono bg-bg px-2 py-0.5 rounded-lg">
          {activeCount}/{agents.length} ACTIVE
        </span>
        <span className="w-2 h-2 rounded-full bg-green animate-pulse" />
      </div>

      <svg viewBox="0 0 420 390" className="w-full">
        <defs>
          {/* Arrowhead marker */}
          <marker id="arrow-active" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="8" markerHeight="6" orient="auto">
            <path d="M0,0 L10,3 L0,6 Z" fill="#f5a623" />
          </marker>
          <marker id="arrow-idle" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="7" markerHeight="5" orient="auto">
            <path d="M0,0 L10,3 L0,6 Z" fill="#e5e7eb" />
          </marker>
          {/* Flowing particle for active edges */}
          <circle id="particle" r="3" fill="#f5a623" />
        </defs>

        {/* Edges */}
        {edges.map((edge, i) => {
          const from = agentPositions[edge.from];
          const to = agentPositions[edge.to];
          if (!from || !to) return null;
          const isActive = edge.active;
          const count = edge.messageCount || 0;

          // Shorten line so it doesn't overlap circles
          const dx = to.x - from.x;
          const dy = to.y - from.y;
          const len = Math.sqrt(dx * dx + dy * dy);
          const offset = 28;
          const sx = from.x + (dx / len) * offset;
          const sy = from.y + (dy / len) * offset;
          const ex = to.x - (dx / len) * offset;
          const ey = to.y - (dy / len) * offset;
          const pathId = `edge-${i}`;

          // midpoint for label
          const mx = (sx + ex) / 2;
          const my = (sy + ey) / 2;

          return (
            <g key={i}>
              <path
                id={pathId}
                d={`M${sx},${sy} L${ex},${ey}`}
                stroke={isActive ? '#f5a623' : '#e5e7eb'}
                strokeWidth={isActive ? 2 : 1}
                strokeDasharray={isActive ? 'none' : '4 4'}
                fill="none"
                markerEnd={isActive ? 'url(#arrow-active)' : 'url(#arrow-idle)'}
                opacity={isActive ? 0.9 : 0.3}
              />
              {/* Flowing particle on active edges */}
              {isActive && (
                <circle r="3" fill="#f5a623" opacity="0.9">
                  <animateMotion dur={`${Math.max(1, 3 - count * 0.2)}s`} repeatCount="indefinite">
                    <mpath href={`#${pathId}`} />
                  </animateMotion>
                </circle>
              )}
              {/* Message count badge */}
              {isActive && count > 0 && (
                <>
                  <rect x={mx - 9} y={my - 7} width="18" height="14" rx="4" fill="#f5a623" opacity="0.15" />
                  <text x={mx} y={my + 3} textAnchor="middle" fill="#f5a623" fontSize="8" fontWeight="700" fontFamily="JetBrains Mono">
                    {count}
                  </text>
                </>
              )}
            </g>
          );
        })}

        {/* Agent Nodes */}
        {agents.map((agent) => {
          const pos = agentPositions[agent.id];
          if (!pos) return null;
          const isCurrent = agent.id === currentAgent;
          const isActive = agent.status === 'active';
          return (
            <g key={agent.id}>
              {/* Pulse ring for current agent */}
              {isCurrent && (
                <circle cx={pos.x} cy={pos.y} r="30" fill="none" stroke={agent.color} strokeWidth="2" opacity="0.4">
                  <animate attributeName="r" values="28;34;28" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.4;0.1;0.4" dur="2s" repeatCount="indefinite" />
                </circle>
              )}
              {/* Glow */}
              <circle cx={pos.x} cy={pos.y} r="28" fill={agent.color} opacity={isActive ? 0.1 : 0.04} />
              <circle
                cx={pos.x} cy={pos.y} r="22"
                fill="#ffffff"
                stroke={isActive ? agent.color : '#d1d5db'}
                strokeWidth={isCurrent ? 2.5 : 1.5}
              />
              {/* Emoji icon */}
              <text x={pos.x} y={pos.y - 4} textAnchor="middle" fontSize="13" dominantBaseline="middle">
                {AGENT_ICONS[agent.id] || '●'}
              </text>
              {/* Name label */}
              <text x={pos.x} y={pos.y + 12} textAnchor="middle" fill={isActive ? agent.color : '#9ca3af'} fontSize="8" fontWeight="600" fontFamily="Outfit">
                {agent.name.toUpperCase()}
              </text>
            </g>
          );
        })}

        {/* Human node (special) */}
        {edges.some((e) => e.to === 'human' && e.active) && (
          <g>
            <circle cx={agentPositions.human.x} cy={agentPositions.human.y} r="20" fill="#fff7ed" stroke="#f5a623" strokeWidth="1.5" strokeDasharray="3 3" />
            <text x={agentPositions.human.x} y={agentPositions.human.y - 3} textAnchor="middle" fontSize="12" dominantBaseline="middle">👤</text>
            <text x={agentPositions.human.x} y={agentPositions.human.y + 13} textAnchor="middle" fill="#f5a623" fontSize="7" fontWeight="600" fontFamily="Outfit">HUMAN</text>
          </g>
        )}
      </svg>

      {/* Agent detail cards */}
      <div className="space-y-1.5 mt-2">
        {agents.map((a) => {
          const isCurrent = a.id === currentAgent;
          return (
            <div
              key={a.id}
              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-xl transition-colors ${
                isCurrent ? 'bg-amber/5 border border-amber/20' : 'bg-bg'
              }`}
            >
              <div
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: a.status === 'active' ? a.color : '#d1d5db' }}
              />
              <span className="text-[10px] font-semibold text-text w-14 truncate">{a.name}</span>
              <span className="text-[9px] text-muted flex-1 truncate font-mono">
                {a.lastAction || 'Idle'}
              </span>
              <span className="text-[9px] font-mono text-muted/60 shrink-0">
                {a.messagesProcessed || 0}
              </span>
            </div>
          );
        })}
      </div>

      {/* Total footer */}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-border">
        <span className="text-[9px] text-muted">Total messages processed</span>
        <span className="text-[10px] font-mono font-semibold text-text">{totalMessages}</span>
      </div>
    </div>
  );
}
