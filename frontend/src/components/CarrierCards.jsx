import { useState, useEffect } from 'react';
import { Building2, TrendingUp } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { getCarriers } from '../services/api';

export default function CarrierCards() {
  const [carriers, setCarriers] = useState([]);

  useEffect(() => {
    getCarriers().then(setCarriers);
  }, []);

  return (
    <div className="bg-surface border border-amber/10 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <Building2 className="w-4 h-4 text-amber" />
        <h3 className="text-sm font-semibold text-text">Carrier Performance</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {carriers.map((c) => {
          const reliColor = c.reliability >= 90 ? 'text-green' : c.reliability >= 85 ? 'text-amber' : 'text-red';
          const trendData = c.trend.map((v, i) => ({ v, i }));

          return (
            <div key={c.id} className="border border-white/5 rounded-lg p-3 bg-bg/40 hover:border-amber/20 transition-all">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-amber/10 flex items-center justify-center text-xs font-bold text-amber">
                    {c.logo}
                  </div>
                  <span className="text-sm font-medium text-text">{c.name}</span>
                </div>
              </div>

              <div className="flex items-end justify-between">
                <div>
                  <div className="text-[10px] text-text/30 uppercase tracking-wider">Reliability</div>
                  <div className={`text-xl font-bold ${reliColor}`}>{c.reliability}%</div>
                </div>
                <div className="w-16 h-8">
                  <ResponsiveContainer>
                    <LineChart data={trendData}>
                      <Line type="monotone" dataKey="v" stroke="#f5a623" strokeWidth={1.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="flex items-center gap-3 mt-2 pt-2 border-t border-white/5">
                <div>
                  <div className="text-[9px] text-text/30">Active</div>
                  <div className="text-xs text-text/70 font-mono">{c.active}</div>
                </div>
                <div>
                  <div className="text-[9px] text-text/30">Delayed</div>
                  <div className="text-xs text-red font-mono">{c.delayed}</div>
                </div>
                <TrendingUp className="w-3 h-3 text-green ml-auto" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
