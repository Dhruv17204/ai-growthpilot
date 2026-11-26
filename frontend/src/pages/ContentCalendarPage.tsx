import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { ContentItem } from '../types';
import {
  Calendar as CalendarIcon,
  Sparkles,
  Plus,
  Trash2,
  Edit2,
  CheckCircle2,
  Clock,
  Send,
  Filter,
  Eye,
  RefreshCw,
  Share2,
  AlertTriangle,
  Cpu
} from 'lucide-react';

const STATUS_BADGES: Record<string, { bg: string; text: string; border: string }> = {
  Draft: { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-200' },
  'Pending Approval': { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200' },
  Approved: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  Published: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
};

const CHANNEL_ICONS: Record<string, string> = {
  LinkedIn: '💼',
  Instagram: '📸',
  Blog: '📝',
  Email: '📧',
  'Google Ads': '🎯',
  Twitter: '🐦',
};

export const ContentCalendarPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: contentItems, isLoading } = useQuery({
    queryKey: ['content-items'],
    queryFn: api.getContent,
  });

  const [viewMode, setViewMode] = useState<'list' | 'weekly' | 'monthly'>('list');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // New Content Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalFormData, setModalFormData] = useState({
    title: '',
    channel: 'LinkedIn',
    publication_date: new Date().toISOString().slice(0, 16),
    status: 'Draft' as ContentItem['status'],
    content_text: '',
    target_audience: 'Founders & Operations Directors',
    tags: '#Tech, #B2B'
  });

  // AI 7-Day Plan Generation
  const generatePlanMutation = useMutation({
    mutationFn: (opts?: { force_demo_mode?: boolean }) =>
      api.generateContentPlan({ days: 7, focus_channel: 'All Channels', force_demo_mode: opts?.force_demo_mode ?? false }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['content-items'] });
      queryClient.invalidateQueries({ queryKey: ['analytics-overview'] });
      const src = data.items[0]?.is_demo ? 'Demo Simulation Mode' : 'Live Gemini AI';
      setToastMessage(`Generated ${data.items.length} new content posts via ${src}!`);
      setTimeout(() => setToastMessage(null), 4000);
    },
    onError: (err: any) => {
      setToastMessage(`AI Generation Note: ${err.message}`);
      setTimeout(() => setToastMessage(null), 5000);
    }
  });

  // Create Content Item Mutation
  const createMutation = useMutation({
    mutationFn: (payload: any) => api.createContentItem(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-items'] });
      setIsModalOpen(false);
      setToastMessage('Content item added to calendar.');
      setTimeout(() => setToastMessage(null), 3000);
    }
  });

  // Update Status Mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.updateContentItem(id, { status: status as any }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-items'] });
      setToastMessage('Status updated.');
      setTimeout(() => setToastMessage(null), 2500);
    }
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteContentItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-items'] });
      setToastMessage('Item deleted.');
      setTimeout(() => setToastMessage(null), 2500);
    }
  });

  const filteredItems = ((contentItems as ContentItem[]) || []).filter((item: ContentItem) => {
    if (statusFilter === 'All') return true;
    return item.status === statusFilter;
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      title: modalFormData.title,
      channel: modalFormData.channel,
      publication_date: new Date(modalFormData.publication_date).toISOString(),
      status: modalFormData.status,
      content_text: modalFormData.content_text,
      target_audience: modalFormData.target_audience,
      tags: modalFormData.tags.split(',').map((t) => t.trim()).filter(Boolean)
    });
  };

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-slate-900 text-white rounded-xl shadow-2xl border border-slate-700 text-xs font-semibold animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Content Calendar</h2>
          <p className="text-xs text-slate-500 mt-1">
            Schedule, approve, and organize multi-channel marketing content. (Published is a workflow status indicator).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => generatePlanMutation.mutate({ force_demo_mode: false })}
            disabled={generatePlanMutation.isPending}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
          >
            {generatePlanMutation.isPending ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            <span>Generate 7-Day Content Plan</span>
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Post</span>
          </button>
        </div>
      </div>

      {generatePlanMutation.isError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 font-medium">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>AI Request Failed: {(generatePlanMutation.error as any)?.message || 'Gemini API failed to generate content plan.'}</span>
          </div>
          <button
            onClick={() => generatePlanMutation.mutate({ force_demo_mode: true })}
            className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shrink-0 transition flex items-center gap-1.5 self-start sm:self-auto"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Generate in Demo Mode Instead</span>
          </button>
        </div>
      )}

      {/* Filters and View Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Status Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {['All', 'Draft', 'Pending Approval', 'Approved', 'Published'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                statusFilter === status
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center bg-white border border-slate-200 rounded-xl p-1 shadow-sm shrink-0">
          {(['list', 'weekly', 'monthly'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                viewMode === mode
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {mode} View
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Presentation */}
      {viewMode === 'list' ? (
        /* List View */
        <div className="space-y-4">
          {filteredItems.length > 0 ? (
            filteredItems.map((item) => (
              <div
                key={item.id}
                className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{CHANNEL_ICONS[item.channel] || '📄'}</span>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                        <span className="font-semibold text-indigo-600">{item.channel}</span>
                        <span>•</span>
                        <span>{new Date(item.publication_date).toLocaleString()}</span>
                        {item.target_audience && (
                          <>
                            <span>•</span>
                            <span>Audience: {item.target_audience}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Status Dropdown */}
                    <select
                      value={item.status}
                      onChange={(e) =>
                        updateStatusMutation.mutate({ id: item.id, status: e.target.value })
                      }
                      className={`text-[11px] font-bold rounded-lg px-2.5 py-1 border outline-none ${
                        STATUS_BADGES[item.status]?.bg
                      } ${STATUS_BADGES[item.status]?.text} ${STATUS_BADGES[item.status]?.border}`}
                    >
                      <option value="Draft">Draft</option>
                      <option value="Pending Approval">Pending Approval</option>
                      <option value="Approved">Approved</option>
                      <option value="Published">Published</option>
                    </select>

                    <button
                      onClick={() => deleteMutation.mutate(item.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-slate-50 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs text-slate-700 whitespace-pre-line leading-relaxed font-sans">
                  {item.content_text}
                </div>

                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {item.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-600"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-3">
              <CalendarIcon className="w-12 h-12 text-slate-300 mx-auto" />
              <h4 className="text-base font-bold text-slate-800">No Content Items Found</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Click "Generate 7-Day Content Plan" to create a week of multi-channel posts with Gemini, or add an individual entry.
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Grid (Weekly / Monthly Calendar View) */
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
              <div key={day} className="text-center font-bold text-xs text-slate-500 pb-2 border-b">
                {day}
              </div>
            ))}
            {filteredItems.slice(0, 14).map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2 hover:border-indigo-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs">{CHANNEL_ICONS[item.channel] || '📄'}</span>
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${STATUS_BADGES[item.status]?.bg} ${STATUS_BADGES[item.status]?.text}`}
                  >
                    {item.status}
                  </span>
                </div>
                <h5 className="text-xs font-bold text-slate-800 line-clamp-2">{item.title}</h5>
                <p className="text-[10px] text-slate-500 line-clamp-3">{item.content_text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal: Add Content Item */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Add Content Calendar Entry</h3>

            <form onSubmit={handleCreateSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Post Title / Hook</label>
                <input
                  type="text"
                  required
                  value={modalFormData.title}
                  onChange={(e) => setModalFormData({ ...modalFormData, title: e.target.value })}
                  placeholder="e.g. Why Custom Workflows Outperform Off-the-Shelf SaaS"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Channel</label>
                  <select
                    value={modalFormData.channel}
                    onChange={(e) => setModalFormData({ ...modalFormData, channel: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="LinkedIn">LinkedIn</option>
                    <option value="Blog">Blog / Case Study</option>
                    <option value="Email">Email Newsletter</option>
                    <option value="Instagram">Instagram</option>
                    <option value="Google Ads">Google Ads</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Status</label>
                  <select
                    value={modalFormData.status}
                    onChange={(e) =>
                      setModalFormData({ ...modalFormData, status: e.target.value as ContentItem['status'] })
                    }
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="Draft">Draft</option>
                    <option value="Pending Approval">Pending Approval</option>
                    <option value="Approved">Approved</option>
                    <option value="Published">Published</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Publication Date & Time</label>
                <input
                  type="datetime-local"
                  required
                  value={modalFormData.publication_date}
                  onChange={(e) => setModalFormData({ ...modalFormData, publication_date: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Content Text</label>
                <textarea
                  rows={4}
                  required
                  value={modalFormData.content_text}
                  onChange={(e) => setModalFormData({ ...modalFormData, content_text: e.target.value })}
                  placeholder="Draft the copy here..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none font-sans"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Tags (comma-separated)</label>
                <input
                  type="text"
                  value={modalFormData.tags}
                  onChange={(e) => setModalFormData({ ...modalFormData, tags: e.target.value })}
                  placeholder="#AI, #B2BGrowth, #Operations"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-md"
                >
                  Save to Calendar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
