import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import {
  Users,
  Award,
  Megaphone,
  Calendar,
  TrendingUp,
  Sparkles,
  ArrowUpRight,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ExternalLink
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Link } from 'react-router-dom';

const PRIORITY_COLORS: Record<string, string> = {
  'High Priority': '#6366F1',
  'Medium Priority': '#F59E0B',
  'Low Priority': '#94A3B8',
};

const SOURCE_COLORS = ['#6366F1', '#8B5CF6', '#EC4899', '#3B82F6', '#10B981', '#F59E0B'];

export const OverviewPage: React.FC = () => {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: api.getAnalyticsOverview,
    refetchInterval: 30000,
  });

  if (isLoading || !analytics) {
    return (
      <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
        <div className="h-28 bg-slate-200/70 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-200/70 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 bg-slate-200/70 rounded-xl animate-pulse" />
          <div className="h-80 bg-slate-200/70 rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  // Transform data for charts
  const categoryData = Object.entries(analytics.leads_by_category || {}).map(([name, value]) => ({
    name,
    value,
  }));

  const sourceData = Object.entries(analytics.leads_by_source || {}).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Demonstration Data Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-indigo-900 via-indigo-950 to-slate-900 p-6 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-violet-600/20 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-500/30 text-violet-200 border border-violet-400/30">
                Portfolio Assessment Mode
              </span>
              <span className="text-xs text-slate-400">Company: NovaTech Solutions</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              AI Growth & Marketing Command Center
            </h2>
            <p className="text-sm text-slate-300 max-w-2xl">
              Centralized workspace for NovaTech Solutions — an agile B2B tech consultancy offering custom AI dev, modern web engineering, and workflow automation across Australia, the US, and India.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <Link
              to="/strategy"
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all flex items-center gap-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>Generate Strategy</span>
            </Link>
            <Link
              to="/campaigns"
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all flex items-center gap-1.5"
            >
              <span>Create Campaign</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Top 5 Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Leads */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Leads</span>
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{analytics.total_leads}</span>
            <span className="text-xs font-medium text-emerald-600 flex items-center">
              <ArrowUpRight className="w-3 h-3" /> +18%
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">Imported & enriched</p>
        </div>

        {/* Qualified Leads */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Qualified Leads</span>
            <div className="p-2 rounded-xl bg-violet-50 text-violet-600">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{analytics.qualified_leads}</span>
            <span className="text-xs font-medium text-indigo-600">
              {analytics.qualification_rate}% rate
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">High priority ICP fit</p>
        </div>

        {/* Active Campaigns */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Campaigns</span>
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <Megaphone className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{analytics.active_campaigns}</span>
            <span className="text-xs font-medium text-blue-600">Multi-Channel</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">Live across LinkedIn & Search</p>
        </div>

        {/* Content Generated */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Content Scheduled</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{analytics.content_generated_count}</span>
            <span className="text-xs font-medium text-emerald-600">Posts</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">In calendar pipeline</p>
        </div>

        {/* Average Lead Score */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Avg Lead Score</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{analytics.average_lead_score}</span>
            <span className="text-xs font-medium text-slate-500">/ 100</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">Objective ICP rubric</p>
        </div>
      </div>

      {/* 4 Interactive Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Lead Acquisition Over Time */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Lead Acquisition Velocity</h3>
              <p className="text-xs text-slate-500">Monthly inbound & qualified lead growth trend</p>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600">
              6-Month Trend
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.lead_acquisition_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="totalLeadsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="qualLeadsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#1E293B', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="leads" name="Total Leads" stroke="#6366F1" strokeWidth={2.5} fillOpacity={1} fill="url(#totalLeadsGrad)" />
                <Area type="monotone" dataKey="qualified" name="Qualified" stroke="#10B981" strokeWidth={2.5} fillOpacity={1} fill="url(#qualLeadsGrad)" />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Lead Distribution by Source */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Leads by Acquisition Source</h3>
              <p className="text-xs text-slate-500">Pipeline attribution breakdown</p>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-700">
              Channel ROI
            </span>
          </div>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sourceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {sourceData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={SOURCE_COLORS[index % SOURCE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#1E293B', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Legend layout="horizontal" verticalAlign="bottom" align="center" iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Campaign Performance */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Campaign Performance</h3>
              <p className="text-xs text-slate-500">Impressions vs. engagement by active campaign</p>
            </div>
            <Link to="/campaigns" className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1">
              View All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.campaign_performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#1E293B', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="clicks" name="Engagements / Clicks" fill="#8B5CF6" radius={[6, 6, 0, 0]} />
                <Bar dataKey="leads" name="Leads Captured" fill="#10B981" radius={[6, 6, 0, 0]} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Lead Qualification Distribution */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Lead Qualification Tiers</h3>
              <p className="text-xs text-slate-500">High vs. Medium vs. Low priority pipeline volume</p>
            </div>
            <Link to="/leads" className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1">
              Lead Intelligence <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {categoryData.map((entry) => (
                    <Cell key={`cell-${entry.name}`} fill={PRIORITY_COLORS[entry.name] || '#94A3B8'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#1E293B', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* AI Growth Recommendations & High Priority Leads */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: High Priority Leads Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Priority Prospect Queue</h3>
              <p className="text-xs text-slate-500">Leads with highest ICP compatibility and immediate deal potential</p>
            </div>
            <Link to="/leads" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
              Explore All <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200/80 text-slate-500 font-semibold">
                  <th className="pb-3">Contact</th>
                  <th className="pb-3">Company & Role</th>
                  <th className="pb-3">Location</th>
                  <th className="pb-3">Fit Score</th>
                  <th className="pb-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {analytics.high_priority_leads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 font-semibold text-slate-900">
                      <div>{lead.name}</div>
                      <div className="text-[11px] text-slate-400 font-normal">{lead.email}</div>
                    </td>
                    <td className="py-3">
                      <div className="font-medium text-slate-800">{lead.company}</div>
                      <div className="text-[11px] text-slate-500">{lead.job_title}</div>
                    </td>
                    <td className="py-3 text-slate-600">{lead.location}</td>
                    <td className="py-3">
                      <div className="flex items-center gap-1.5">
                        <span className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center border border-indigo-200">
                          {lead.score}
                        </span>
                        <span className="text-[10px] uppercase font-bold text-indigo-600 bg-indigo-50/50 px-1.5 py-0.5 rounded">
                          High
                        </span>
                      </div>
                    </td>
                    <td className="py-3">
                      <Link
                        to={`/leads?search=${encodeURIComponent(lead.name)}`}
                        className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 font-medium text-[11px] transition-all"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right 1 Col: AI Recommendations & Recent Activities */}
        <div className="space-y-6">
          {/* AI Growth Recommendations */}
          <div className="bg-gradient-to-br from-violet-50 to-indigo-50 border border-violet-200/80 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 rounded-lg bg-violet-600 text-white">
                <Lightbulb className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-bold text-slate-900">AI Growth Recommendations</h4>
            </div>
            <ul className="space-y-3 text-xs text-slate-700">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-600 mt-1.5 shrink-0" />
                <span>
                  <strong>LinkedIn Lead Surge:</strong> 4 high-priority Operations Directors from Sydney engaged with AI automation topics. Launch Variant B direct outreach.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-600 mt-1.5 shrink-0" />
                <span>
                  <strong>Content Calendar Gap:</strong> No blog case study scheduled for Thursday. Generate Day 4 content piece to sustain SEO momentum.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-600 mt-1.5 shrink-0" />
                <span>
                  <strong>Prompt Optimization:</strong> Switch to Prompt v3.0 for Campaign Studio to maintain zero-hallucination compliance.
                </span>
              </li>
            </ul>
          </div>

          {/* Recent AI Activities */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-bold text-slate-900">Recent AI Activities</h4>
              <Clock className="w-4 h-4 text-slate-400" />
            </div>
            <div className="space-y-3">
              {analytics.recent_activities.slice(0, 4).map((act) => (
                <div key={act.id} className="text-xs border-l-2 border-indigo-400 pl-3 py-0.5">
                  <p className="font-semibold text-slate-800">{act.title}</p>
                  <p className="text-[11px] text-slate-500 truncate">{act.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
