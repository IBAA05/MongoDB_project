import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Database, Edit3, Search, BarChart3 } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/database', label: 'Database', icon: Database },
  { path: '/crud', label: 'CRUD Operations', icon: Edit3 },
  { path: '/search', label: 'Advanced Search', icon: Search },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-slate-900 text-slate-300 flex flex-col z-20">
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <h1 className="text-xl font-bold font-sans text-white tracking-tight flex items-center gap-2">
          <Database className="w-5 h-5 text-primary-500" />
          MongoDash
        </h1>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors font-medium text-sm ${
                  isActive
                    ? 'bg-primary-500/10 text-primary-400'
                    : 'hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500">
        Connected to <span className="text-emerald-400 font-mono">localhost:8000</span>
      </div>
    </aside>
  );
}
