import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Lead, CSVImportResult } from '../types';
import {
  Users,
  Upload,
  Download,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowUpDown,
  RefreshCw,
  X,
  FileSpreadsheet,
  Building,
  MapPin,
  Briefcase,
  Layers,
  ChevronRight,
  TrendingUp,
  MessageSquare,
  Cpu
} from 'lucide-react';

const CATEGORY_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  'High Priority': { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  'Medium Priority': { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  'Low Priority': { bg: 'bg-slate-100', text: 'text-slate-600', border: 'border-slate-200' },
};

export const LeadIntelligencePage: React.FC = () => {
  const queryClient = useQueryClient();

  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [sortBy, setSortBy] = useState('score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // CSV Upload Dialog State
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadResult, setUploadResult] = useState<CSVImportResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // New Note State
  const [noteInput, setNoteInput] = useState('');

  // Fetch leads
  const { data: leads, isLoading } = useQuery({
    queryKey: ['leads', search, categoryFilter, statusFilter, sortBy, sortOrder],
    queryFn: () => api.getLeads({
      search,
      category: categoryFilter,
      status: statusFilter,
      sort_by: sortBy,
      sort_order: sortOrder
    }),
  });

  // Score Recalculation Mutation
  const scoreMutation = useMutation({
    mutationFn: ({ leadId, force_demo_mode }: { leadId: number; force_demo_mode?: boolean }) =>
      api.recalculateLeadScore(leadId, force_demo_mode ?? false),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['analytics-overview'] });
      if (selectedLead && selectedLead.id === data.result.lead_id) {
        setSelectedLead({
          ...selectedLead,
          score: data.result.score,
          qualification_category: data.result.qualification_category,
          business_fit_summary: data.result.business_fit_summary,
          suggested_next_action: data.result.suggested_next_action,
          score_explanation: data.result.score_explanation,
        });
      }
      setToastMessage('Lead score updated via ICP analysis!');
      setTimeout(() => setToastMessage(null), 3000);
    },
    onError: (err: any) => {
      setToastMessage(`Scoring Note: ${err.message}`);
      setTimeout(() => setToastMessage(null), 5000);
    }
  });

  // Add Note Mutation
  const addNoteMutation = useMutation({
    mutationFn: ({ leadId, text }: { leadId: number; text: string }) =>
      api.addLeadNote(leadId, text),
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      if (selectedLead) {
        setSelectedLead({
          ...selectedLead,
          notes: [...(selectedLead.notes || []), note],
        });
      }
      setNoteInput('');
      setToastMessage('Note added.');
      setTimeout(() => setToastMessage(null), 2500);
    }
  });

  // Update Status Mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ leadId, status }: { leadId: number; status: string }) =>
      api.updateLead(leadId, { status: status as any }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setSelectedLead(updated);
      setToastMessage('Lead status updated.');
      setTimeout(() => setToastMessage(null), 2500);
    }
  });

  // CSV File Handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadResult(null);

    try {
      const result = await api.importLeadsCSV(file);
      setUploadResult(result);
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['analytics-overview'] });
      setToastMessage(`Imported ${result.successful_imports} new leads!`);
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err: any) {
      setToastMessage(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
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
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Lead Intelligence</h2>
          <p className="text-xs text-slate-500 mt-1">
            CSV import, objective ICP scoring rubric, explainable attribution factors, and qualification pipeline.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
          >
            <Upload className="w-4 h-4" />
            <span>Import CSV Leads</span>
          </button>
          <a
            href={api.exportLeadsCSVUrl()}
            download
            className="px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-bold text-xs shadow-sm transition-all flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-wrap items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, company, email, job title..."
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-semibold">Priority:</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 outline-none"
            >
              <option value="All">All Tiers</option>
              <option value="High Priority">High Priority</option>
              <option value="Medium Priority">Medium Priority</option>
              <option value="Low Priority">Low Priority</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 outline-none"
            >
              <option value="All">All Statuses</option>
              <option value="New">New</option>
              <option value="Contacted">Contacted</option>
              <option value="In Discussion">In Discussion</option>
              <option value="Qualified">Qualified</option>
              <option value="Disqualified">Disqualified</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-semibold">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 outline-none"
            >
              <option value="score">Fit Score</option>
              <option value="name">Name</option>
              <option value="company">Company</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-600"
              title="Toggle Sort Order"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Table & Slide-over Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Table View (7 or 12 Cols depending on selection) */}
        <div className={`${selectedLead ? 'lg:col-span-7' : 'lg:col-span-12'} bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden transition-all`}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200/80 text-slate-500 font-semibold">
                <tr>
                  <th className="py-3 px-4">Lead Contact</th>
                  <th className="py-3 px-4">Company & Industry</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4">Score</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {leads && leads.length > 0 ? (
                  leads.map((lead) => {
                    const style = CATEGORY_STYLES[lead.qualification_category] || CATEGORY_STYLES['Low Priority'];
                    const isSelected = selectedLead?.id === lead.id;

                    return (
                      <tr
                        key={lead.id}
                        onClick={() => setSelectedLead(lead)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? 'bg-indigo-50/60' : 'hover:bg-slate-50/70'
                        }`}
                      >
                        <td className="py-3.5 px-4 font-semibold text-slate-900">
                          <div>{lead.name}</div>
                          <div className="text-[11px] text-slate-400 font-normal">{lead.email}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-medium text-slate-800">{lead.company}</div>
                          <div className="text-[11px] text-slate-500">{lead.industry} • {lead.job_title}</div>
                        </td>
                        <td className="py-3.5 px-4 text-slate-600">{lead.location || 'Global'}</td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <span className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center border border-indigo-200">
                              {lead.score}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${style.bg} ${style.text} ${style.border}`}>
                              {lead.qualification_category.replace(' Priority', '')}
                            </span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="text-[11px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                            {lead.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <ChevronRight className="w-4 h-4 text-slate-400 ml-auto" />
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No leads match your filter criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Slide-over Detail Panel (5 Cols) */}
        {selectedLead && (
          <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 shadow-lg p-6 space-y-6 h-fit animate-fade-in">
            <div className="flex items-start justify-between">
              <div>
                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                  CATEGORY_STYLES[selectedLead.qualification_category]?.bg
                } ${CATEGORY_STYLES[selectedLead.qualification_category]?.text} ${
                  CATEGORY_STYLES[selectedLead.qualification_category]?.border
                }`}>
                  {selectedLead.qualification_category}
                </span>
                <h3 className="text-lg font-bold text-slate-900 mt-2">{selectedLead.name}</h3>
                <p className="text-xs text-slate-500">{selectedLead.job_title} at {selectedLead.company}</p>
              </div>

              <button
                onClick={() => setSelectedLead(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* AI Score Breakdown Header */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                  Objective Fit Score
                </span>
                <div className="text-3xl font-black text-indigo-600 mt-0.5">{selectedLead.score} <span className="text-xs font-normal text-slate-400">/ 100</span></div>
              </div>

              <button
                onClick={() => scoreMutation.mutate({ leadId: selectedLead.id, force_demo_mode: false })}
                disabled={scoreMutation.isPending}
                className="px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${scoreMutation.isPending ? 'animate-spin' : ''}`} />
                <span>Re-score AI</span>
              </button>
            </div>

            {scoreMutation.isError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs space-y-1.5">
                <div className="flex items-center gap-1.5 font-bold text-rose-700">
                  <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                  <span>AI Scoring Request Failed</span>
                </div>
                <p className="text-[11px] leading-relaxed">{(scoreMutation.error as any)?.message}</p>
                <button
                  type="button"
                  onClick={() => scoreMutation.mutate({ leadId: selectedLead.id, force_demo_mode: true })}
                  className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition flex items-center gap-1"
                >
                  <Cpu className="w-3 h-3" />
                  <span>Score in Demo Mode Instead</span>
                </button>
              </div>
            )}

            {/* Strategic Fit & Suggested Action */}
            <div className="space-y-3 text-xs">
              <div className="p-3.5 rounded-xl bg-violet-50/60 border border-violet-100">
                <span className="font-bold text-violet-900 block mb-1">Potential Business Fit</span>
                <p className="text-violet-800 leading-relaxed">
                  {selectedLead.business_fit_summary || 'Analysis pending score evaluation.'}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-100">
                <span className="font-bold text-emerald-900 block mb-1">Recommended Next Action</span>
                <p className="text-emerald-800 leading-relaxed">
                  {selectedLead.suggested_next_action || 'Review prospect online profile before reaching out.'}
                </p>
              </div>
            </div>

            {/* Transparent Factor Breakdown */}
            {selectedLead.score_explanation && Object.keys(selectedLead.score_explanation).length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-800 block">Explainable Attribution Rubric</span>
                <div className="space-y-2">
                  {Object.entries(selectedLead.score_explanation).map(([factor, item]: [string, any]) => (
                    <div key={factor} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-700 capitalize">
                          {factor.replace(/_/g, ' ')}
                        </span>
                        <span className="font-bold text-indigo-600">
                          {item.score} / {item.max}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">{item.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Lead Status Selector */}
            <div className="pt-2 border-t border-slate-100">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Pipeline Stage</label>
              <select
                value={selectedLead.status}
                onChange={(e) => updateStatusMutation.mutate({ leadId: selectedLead.id, status: e.target.value })}
                className="w-full text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium text-slate-700 outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="New">New</option>
                <option value="Contacted">Contacted</option>
                <option value="In Discussion">In Discussion</option>
                <option value="Qualified">Qualified</option>
                <option value="Disqualified">Disqualified</option>
              </select>
            </div>

            {/* Notes Section */}
            <div className="pt-2 border-t border-slate-100 space-y-3">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
                <span>Internal Notes ({selectedLead.notes?.length || 0})</span>
              </span>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {(selectedLead.notes || []).map((n) => (
                  <div key={n.id} className="p-2.5 rounded-lg bg-slate-50 text-xs border border-slate-100">
                    <p className="text-slate-800">{n.note_text}</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      {new Date(n.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  placeholder="Add note on discovery call or objections..."
                  className="flex-1 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white"
                />
                <button
                  onClick={() => addNoteMutation.mutate({ leadId: selectedLead.id, text: noteInput })}
                  disabled={!noteInput.trim() || addNoteMutation.isPending}
                  className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                >
                  Post
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* CSV Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-indigo-600" />
                <span>Import Leads from CSV</span>
              </h3>
              <button
                onClick={() => setIsUploadOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Upload a CSV file containing target prospect leads. Expected columns:
              <span className="font-semibold text-slate-700"> Name, Company, Email, Industry, Job Title, Location, Company Size, Lead Source</span>.
            </p>

            {/* Dropzone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl p-8 text-center cursor-pointer transition-all bg-slate-50/50 hover:bg-indigo-50/30"
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".csv"
                className="hidden"
              />
              <Upload className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
              <p className="text-xs font-bold text-slate-800">
                {isUploading ? 'Validating and importing leads...' : 'Click to select CSV file'}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">Maximum file size 5MB • Standard CSV format</p>
            </div>

            {/* Upload Feedback Result */}
            {uploadResult && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold text-emerald-700">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Import Completed</span>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-1 text-center font-semibold">
                  <div className="p-2 rounded-lg bg-white border border-slate-200">
                    <span className="text-slate-400 text-[10px] block">Total Rows</span>
                    <span className="text-slate-900 text-sm">{uploadResult.total_rows}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200">
                    <span className="text-emerald-600 text-[10px] block">Imported</span>
                    <span className="text-emerald-700 text-sm">{uploadResult.successful_imports}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-amber-50 border border-amber-200">
                    <span className="text-amber-600 text-[10px] block">Duplicates</span>
                    <span className="text-amber-700 text-sm">{uploadResult.duplicate_count}</span>
                  </div>
                </div>

                {uploadResult.errors.length > 0 && (
                  <div className="text-[11px] text-rose-600 bg-rose-50 p-2 rounded-lg mt-2 space-y-1">
                    <span className="font-bold">Errors encountered:</span>
                    {uploadResult.errors.map((err, i) => (
                      <div key={i}>• {err}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end gap-2.5 pt-2">
              <button
                onClick={() => setIsUploadOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
