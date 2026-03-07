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
    <div className="bg-surface border border-border rounded-2xl p-5 shadow-card">
      <div className="flex items-center gap-2 mb-4">
        <Building2 className="w-4 h-4 text-amber" />
        <h3 className="text-sm font-semibold text-text">Carrier Performance</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {carriers.length === 0 ? (
          <div className="col-span-full flex flex-col items-center justify-center py-12 text-center">
            <Building2 className="w-8 h-8 text-muted/30 mb-2" />
            <p className="text-xs text-muted">No carrier data available</p>
            <p className="text-[10px] text-muted/60 mt-1">Carrier performance will appear after running a simulation</p>
          </div>
        ) : (carriers.map((c) => {
          const reliColor = c.reliability >= 90 ? 'text-green' : c.reliability >= 85 ? 'text-amber' : 'text-red';
          const trendData = c.trend.map((v, i) => ({ v, i }));

          return (
            <div key={c.id} className="border border-border rounded-2xl p-4 bg-surface hover:shadow-card-hover transition-all">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-xl bg-amber/10 flex items-center justify-center text-xs font-bold text-amber">
                    {c.logo}
                  </div>
                  <span className="text-sm font-medium text-text">{c.name}</span>
                </div>
              </div>

              <div className="flex items-end justify-between">
                <div>
                  <div className="text-[10px] text-muted uppercase tracking-wider">Reliability</div>
                  <div className={`text-2xl font-bold ${reliColor}`}>{c.reliability}%</div>
                </div>
                <div className="w-16 h-8">
                  <ResponsiveContainer>
                    <LineChart data={trendData}>
                      <Line type="monotone" dataKey="v" stroke="#f5a623" strokeWidth={1.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border">
                <div>
                  <div className="text-[9px] text-muted">Active</div>
                  <div className="text-xs text-text/80 font-mono">{c.active}</div>
                </div>
                <div>
                  <div className="text-[9px] text-muted">Delayed</div>
                  <div className="text-xs text-red font-mono">{c.delayed}</div>
                </div>
                <TrendingUp className="w-3 h-3 text-green ml-auto" />
              </div>
            </div>
          );
        }))}
      </div>
    </div>
  );
}
