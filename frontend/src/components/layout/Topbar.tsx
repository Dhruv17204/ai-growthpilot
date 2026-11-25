import React from 'react';
import { Menu, Sparkles, AlertCircle, CheckCircle2, Shield, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

interface TopbarProps {
  title: string;
  subtitle?: string;
  onOpenSidebar: () => void;
  aiStatus?: string;
  isDemoMode?: boolean;
}

export const Topbar: React.FC<TopbarProps> = ({
  title,
  subtitle,
  onOpenSidebar,
  aiStatus = 'connected',
  isDemoMode = true,
}) => {
  const isLive = aiStatus === 'connected' && !isDemoMode;

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-8 py-3.5 transition-all">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Mobile hamburger + Titles */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenSidebar}
            className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:outline-none"
            aria-label="Toggle Navigation"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h1>
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
        </div>

        {/* Right: AI System Status & Settings shortcut */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Demo Data indicator */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            <span>Demo Data: NovaTech Solutions</span>
          </div>

          {/* AI Connection status pill */}
          <Link
            to="/settings"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
              isLive
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300 hover:bg-emerald-100'
                : 'bg-violet-50 text-violet-700 border-violet-200 hover:bg-violet-100'
            }`}
          >
            {isLive ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Gemini API Live</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-violet-600" />
                <span>Simulation / Demo Mode</span>
              </>
            )}
          </Link>
        </div>
      </div>
    </header>
  );
};
