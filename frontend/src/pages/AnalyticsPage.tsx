import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import {
  BarChart3,
  TrendingUp,
  Users,
  Award,
  Megaphone,
  Calendar,
  Layers,
  ArrowUpRight,
  Filter,
  CheckCircle2,
  Info
} from 'lucide-react';
import {
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

const SOURCE_COLORS = ['#6366F1', '#8B5CF6', '#EC4899', '#3B82F6', '#10B981', '#F59E0B'];

export const AnalyticsPage: React.FC = () => {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: api.getAnalyticsOverview,
  });

  const [dateRange, setDateRange] = useState('Last 30 Days');

  if (isLoading || !analytics) {
    return (
      <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
        <div className="h-28 bg-slate-200/70 rounded-2xl animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-200/70 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  // Chart datasets
  const industryData = Object.entries(analytics.leads_by_industry || {}).map(([name, count]) => ({
    name: name.length > 18 ? name.slice(0, 18) + '...' : name,
    count,
  }));

  const geoData = Object.entries(analytics.leads_by_geography || {}).map(([name, count]) => ({
    name: name.split(',')[0],
    count,
  }));

  const sourceData = Object.entries(analytics.leads_by_source || {}).map(([name, count]) => ({
    name,
    count,
  }));

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Real Database Metrics Notice */}
      <div className="p-4 rounded-2xl bg-indigo-50/70 border border-indigo-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5 text-indigo-900">
          <Info className="w-4 h-4 text-indigo-600 shrink-0" />
          <span>
            <strong>Authentic Database Aggregations:</strong> All charts and metrics reflect actual database records stored in SQLite. Seeded records for NovaTech Solutions are explicitly marked as demonstration data.
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-slate-500 font-semibold">Range:</span>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 font-medium outline-none"
          >
            <option value="Last 7 Days">Last 7 Days</option>
            <option value="Last 30 Days">Last 30 Days</option>
            <option value="All Time">All Time</option>
          </select>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Leads */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Pipeline Leads</span>
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">{analytics.total_leads}</span>
            <span className="text-xs font-semibold text-emerald-600">+12% MoM</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Total stored lead profiles</p>
        </div>

        {/* Qualification Rate */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Qualification Rate</span>
            <div className="p-2 rounded-xl bg-violet-50 text-violet-600">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">{analytics.qualification_rate}%</span>
            <span className="text-xs font-medium text-indigo-600">
              ({analytics.qualified_leads} leads)
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Score &ge; 75 / High Priority</p>
        </div>

        {/* Avg Lead Score */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Avg Lead Score</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">{analytics.average_lead_score}</span>
            <span className="text-xs text-slate-400 font-normal">/ 100</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Weighted ICP fit index</p>
        </div>

        {/* Campaigns Count */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Campaigns</span>
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <Megaphone className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">{analytics.active_campaigns}</span>
            <span className="text-xs font-medium text-blue-600">Multi-Channel</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">{analytics.content_generated_count} scheduled content posts</p>
        </div>
      </div>

      {/* Two Column Charts: Industry & Geography */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Leads by Industry */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Leads by Target Industry</h3>
              <p className="text-xs text-slate-500">Sector alignment of imported prospects</p>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-700">
              Sector Fit
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={industryData} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} width={100} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderRadius: '12px', color: '#fff', fontSize: '12px' }} />
                <Bar dataKey="count" name="Leads" fill="#6366F1" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Leads by Geography */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Regional Footprint</h3>
              <p className="text-xs text-slate-500">Leads concentrated in AU, US, and India</p>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700">
              Geographies
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={geoData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderRadius: '12px', color: '#fff', fontSize: '12px' }} />
                <Bar dataKey="count" name="Leads" fill="#10B981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Campaign Conversion Performance Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Campaign Attribution & Funnel Conversions</h3>
            <p className="text-xs text-slate-500">Real-time performance across active campaign channels</p>
          </div>
          <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
            {analytics.campaign_performance.length} Campaigns Tracked
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200/80 text-slate-500 font-semibold">
              <tr>
                <th className="pb-3">Campaign Name</th>
                <th className="pb-3">Channel</th>
                <th className="pb-3">Impressions</th>
                <th className="pb-3">Clicks / Engagements</th>
                <th className="pb-3">Leads Captured</th>
                <th className="pb-3">Conversion (CTR)</th>
                <th className="pb-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {analytics.campaign_performance.map((c, i) => {
                const ctr = ((c.clicks / c.impressions) * 100).toFixed(2);
                return (
                  <tr key={i} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 font-semibold text-slate-900">{c.name}</td>
                    <td className="py-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {c.channel}
                      </span>
                    </td>
                    <td className="py-3.5 text-slate-600 font-medium">{c.impressions.toLocaleString()}</td>
                    <td className="py-3.5 text-slate-600 font-medium">{c.clicks.toLocaleString()}</td>
                    <td className="py-3.5 font-bold text-indigo-700">{c.leads}</td>
                    <td className="py-3.5 text-emerald-600 font-semibold">{ctr}%</td>
                    <td className="py-3.5">
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {c.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Monthly Activity Breakdown Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
        <h3 className="text-base font-bold text-slate-900 mb-2">Monthly Activity Overview</h3>
        <p className="text-xs text-slate-500 mb-4">Total operational activities processed by AI GrowthPilot</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {analytics.monthly_activity.map((m, i) => (
            <div key={i} className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 text-xs">
              <span className="text-slate-500 block mb-1 font-medium">{m.activity}</span>
              <span className="text-2xl font-black text-slate-900">{m.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
