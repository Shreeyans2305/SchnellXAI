import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, Truck, FlaskConical, Building2, GraduationCap, Settings } from 'lucide-react';

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
    <aside className="w-16 bg-sidebar flex flex-col items-center py-6 shrink-0 rounded-r-3xl shadow-lg z-10">
      {/* Logo */}
      <div className="w-10 h-10 rounded-xl bg-amber/20 flex items-center justify-center mb-8">
        <span className="text-amber font-bold text-lg">C</span>
      </div>

      <nav className="flex flex-col gap-2 items-center flex-1">
        {navItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.to}
            title={item.label}
            className={({ isActive }) =>
              `w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-amber text-sidebar shadow-md'
                  : 'text-white/40 hover:text-white hover:bg-white/10'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto flex flex-col gap-3 items-center">
        <div className="w-2 h-2 rounded-full bg-green animate-pulse" title="System Online" />
        <button className="w-10 h-10 flex items-center justify-center rounded-xl text-white/30 hover:text-white hover:bg-white/10 transition-all">
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </aside>
  );
}
