import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, Truck, FlaskConical, Building2, GraduationCap } from 'lucide-react';

const navItems = [
  { label: 'Command Center', icon: LayoutDashboard, to: '/dashboard' },
  { label: 'Agents', icon: Bot, to: '/dashboard', section: 'agents' },
  { label: 'Shipments', icon: Truck, to: '/dashboard', section: 'shipments' },
  { label: 'Simulation', icon: FlaskConical, to: '/simulation' },
  { label: 'Carriers', icon: Building2, to: '/dashboard', section: 'carriers' },
  { label: 'Learn', icon: GraduationCap, to: '/dashboard', section: 'learn' },
];

export default function Sidebar() {
  return (
    <aside className="w-16 lg:w-52 bg-surface border-r border-amber/10 flex flex-col py-4 shrink-0">
      <nav className="flex flex-col gap-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group ${
                isActive
                  ? 'bg-amber/10 text-amber border border-amber/20'
                  : 'text-text/50 hover:text-text/80 hover:bg-white/5 border border-transparent'
              }`
            }
          >
            <item.icon className="w-4 h-4 shrink-0" />
            <span className="hidden lg:block">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto px-4 hidden lg:block">
        <div className="border border-amber/10 rounded-lg p-3 bg-bg/40">
          <div className="text-[10px] text-text/30 uppercase tracking-wider mb-1">System</div>
          <div className="text-xs text-text/60">v2.4.1 • production</div>
          <div className="flex items-center gap-1 mt-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green" />
            <span className="text-[10px] text-green">All systems operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
