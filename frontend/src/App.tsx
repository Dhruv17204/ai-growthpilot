import React, { useState, Suspense } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { Topbar } from './components/layout/Topbar';
import { useQuery } from '@tanstack/react-query';
import { api } from './api/client';

// Code-split route components for optimized bundle performance
const OverviewPage = React.lazy(() => import('./pages/OverviewPage').then(m => ({ default: m.OverviewPage })));
const StrategyPage = React.lazy(() => import('./pages/StrategyPage').then(m => ({ default: m.StrategyPage })));
const CampaignStudioPage = React.lazy(() => import('./pages/CampaignStudioPage').then(m => ({ default: m.CampaignStudioPage })));
const ContentCalendarPage = React.lazy(() => import('./pages/ContentCalendarPage').then(m => ({ default: m.ContentCalendarPage })));
const LeadIntelligencePage = React.lazy(() => import('./pages/LeadIntelligencePage').then(m => ({ default: m.LeadIntelligencePage })));
const AnalyticsPage = React.lazy(() => import('./pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const PromptLabPage = React.lazy(() => import('./pages/PromptLabPage').then(m => ({ default: m.PromptLabPage })));
const SettingsPage = React.lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));

const PageLoadingFallback: React.FC = () => (
  <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-6 animate-pulse">
    <div className="h-24 bg-slate-200/70 rounded-2xl" />
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <div className="h-32 bg-slate-200/70 rounded-xl" />
      <div className="h-32 bg-slate-200/70 rounded-xl" />
      <div className="h-32 bg-slate-200/70 rounded-xl" />
    </div>
    <div className="h-80 bg-slate-200/70 rounded-2xl" />
  </div>
);

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': {
    title: 'Overview Dashboard',
    subtitle: 'Unified AI marketing operations and pipeline command center',
  },
  '/strategy': {
    title: 'AI Growth Strategy',
    subtitle: 'Formulate 30-day marketing roadmaps, ICP definitions, and channel allocations',
  },
  '/campaigns': {
    title: 'Campaign Studio',
    subtitle: 'Generate multi-angle copy and distribution schedules across channels',
  },
  '/calendar': {
    title: 'Content Calendar',
    subtitle: 'Review, approve, and manage scheduled multi-channel content publications',
  },
  '/leads': {
    title: 'Lead Intelligence',
    subtitle: 'CSV import, explainable ICP scoring rubric, and prospective buyer qualification',
  },
  '/analytics': {
    title: 'Growth Analytics',
    subtitle: 'Live SQLite database aggregations and campaign conversion performance',
  },
  '/prompt-lab': {
    title: 'Prompt Engineering Lab',
    subtitle: 'Iterative prompt evolution benchmarks (v1, v2, v3) and generation audit logs',
  },
  '/settings': {
    title: 'System Settings',
    subtitle: 'AI model parameters, safe API health diagnostics, and demo data management',
  },
};

export const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  });

  const { data: profile } = useQuery({
    queryKey: ['business-profile'],
    queryFn: api.getBusinessProfile,
  });

  const currentMeta = PAGE_TITLES[location.pathname] || {
    title: 'AI GrowthPilot',
    subtitle: 'AI-Powered Business Growth Platform',
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Dark Navy Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        businessName={profile?.company_name || 'NovaTech Solutions'}
        isDemoMode={health?.demo_mode ?? true}
      />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <Topbar
          title={currentMeta.title}
          subtitle={currentMeta.subtitle}
          onOpenSidebar={() => setSidebarOpen(true)}
          aiStatus={health?.ai_status || 'connected'}
          isDemoMode={health?.demo_mode ?? true}
        />

        <main className="flex-1 pb-16">
          <Suspense fallback={<PageLoadingFallback />}>
            <Routes>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/strategy" element={<StrategyPage />} />
              <Route path="/campaigns" element={<CampaignStudioPage />} />
              <Route path="/calendar" element={<ContentCalendarPage />} />
              <Route path="/leads" element={<LeadIntelligencePage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/prompt-lab" element={<PromptLabPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
};

export default App;
