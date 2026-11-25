import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Compass,
  Megaphone,
  Calendar,
  Users,
  BarChart3,
  Cpu,
  Settings,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  Building2,
  X
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  businessName?: string;
  isDemoMode?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  businessName = 'NovaTech Solutions',
  isDemoMode = true,
}) => {
  const navItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard, badge: null },
    { name: 'AI Strategy', path: '/strategy', icon: Compass, badge: 'AI' },
    { name: 'Campaign Studio', path: '/campaigns', icon: Megaphone, badge: null },
    { name: 'Content Calendar', path: '/calendar', icon: Calendar, badge: null },
    { name: 'Lead Intelligence', path: '/leads', icon: Users, badge: 'Scoring' },
    { name: 'Analytics', path: '/analytics', icon: BarChart3, badge: null },
    { name: 'Prompt Lab', path: '/prompt-lab', icon: Cpu, badge: 'v3.0' },
    { name: 'Settings', path: '/settings', icon: Settings, badge: null },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 w-64 bg-[#0B0F19] text-slate-300 z-50 flex flex-col border-r border-slate-800/80 transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Top Brand Header */}
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 via-indigo-600 to-purple-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-base tracking-tight">GrowthPilot</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/30">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Marketing & Growth Ops</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Business Selector Pill */}
        <div className="px-4 py-3 border-b border-slate-800/60 bg-slate-900/40">
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-7 h-7 rounded-md bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
                <Building2 className="w-4 h-4" />
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-slate-200 truncate">{businessName}</p>
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="text-[10px] text-slate-400">
                    {isDemoMode ? 'Demo Workspace' : 'Production Workspace'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Workspace Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-gradient-to-r from-violet-600/20 to-indigo-600/10 text-white font-semibold border-l-2 border-violet-500 shadow-sm'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-violet-900/60 text-violet-300 border border-violet-700/50">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer / AI Engine Status */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/60">
          <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/40">
            <div className="flex items-center justify-between text-xs font-medium text-slate-300 mb-1.5">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-violet-400" />
                Gemini GenAI
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300">
                gemini-2.5-flash
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Anti-hallucination structured prompt schemas v3.0 active.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
};
