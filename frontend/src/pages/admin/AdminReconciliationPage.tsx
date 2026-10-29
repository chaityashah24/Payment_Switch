import React, { useEffect, useState } from 'react';
import { Scale, Play, AlertCircle, CheckCircle2, ShieldAlert, FileText, Check } from 'lucide-react';
import { api } from '../../services/api';
import { ReconciliationRun, ReconciliationException } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const AdminReconciliationPage: React.FC = () => {
  const [runs, setRuns] = useState<ReconciliationRun[]>([]);
  const [exceptions, setExceptions] = useState<ReconciliationException[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  // Exception resolution state
  const [selectedException, setSelectedException] = useState<ReconciliationException | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('Discrepancy verified against simulated core banking logs and resolved.');
  const [resolving, setResolving] = useState(false);

  const loadData = async () => {
    try {
      const [rRes, excRes] = await Promise.all([
        api.getReconciliationRuns(),
        api.getReconciliationExceptions(),
      ]);
      setRuns(rRes);
      setExceptions(excRes);
    } catch (err) {
      console.error('Failed to load reconciliation data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTriggerRun = async () => {
    setRunning(true);
    setMsg(null);
    try {
      const now = new Date();
      const past = new Date();
      past.setDate(past.getDate() - 7);

      const run = await api.triggerReconciliation({
        period_start: past.toISOString(),
        period_end: now.toISOString(),
      });
      setMsg(`Reconciliation run ${run.run_reference} completed. ${run.total_matched} matched, ${run.total_exceptions} exceptions.`);
      await loadData();
    } catch (err: any) {
      setMsg(`Run failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleResolveException = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedException) return;
    setResolving(true);
    try {
      await api.resolveException(selectedException.id, {
        resolution_notes: resolutionNotes,
        mark_as: 'RESOLVED',
      });
      setSelectedException(null);
      await loadData();
    } catch (err) {
      console.error('Failed to resolve exception:', err);
    } finally {
      setResolving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading reconciliation engine...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">3-Way Reconciliation</h1>
          <p className="text-xs text-slate-500">Cross-verifies Switch transactions vs Bank Core records vs Ledger postings</p>
        </div>
        <button
          onClick={handleTriggerRun}
          disabled={running}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold shadow-md transition-all disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
          <span>{running ? 'Reconciling Records...' : 'Run 3-Way Match'}</span>
        </button>
      </div>

      {msg && (
        <div className="p-4 bg-slate-900 text-teal-300 rounded-2xl text-xs font-mono flex items-center justify-between">
          <span>{msg}</span>
          <button onClick={() => setMsg(null)} className="text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Exceptions List */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base text-slate-900">Detected Reconciliation Discrepancies</h2>
            <p className="text-xs text-slate-500">Exceptions flagged by the three-way comparison engine</p>
          </div>
          <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full">
            {exceptions.filter((e) => e.status !== 'RESOLVED').length} Open Exceptions
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Exception Type</th>
                <th className="px-5 py-3">Severity</th>
                <th className="px-5 py-3">Reference Key</th>
                <th className="px-5 py-3">Explanation</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {exceptions.map((exc) => (
                <tr key={exc.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3.5 font-bold text-slate-900 font-mono text-[11px]">
                    {exc.exception_type}
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        exc.severity === 'CRITICAL'
                          ? 'bg-rose-100 text-rose-800'
                          : exc.severity === 'HIGH'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {exc.severity}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-600">{exc.reference_key || exc.payment_id || '—'}</td>
                  <td className="px-5 py-3.5 text-slate-700 max-w-sm">{exc.explanation}</td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={exc.status} />
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    {exc.status !== 'RESOLVED' ? (
                      <button
                        onClick={() => setSelectedException(exc)}
                        className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold"
                      >
                        Investigate & Resolve
                      </button>
                    ) : (
                      <span className="text-slate-400 font-mono text-[11px]">Resolved</span>
                    )}
                  </td>
                </tr>
              ))}
              {exceptions.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400">
                    All records match across Switch, Bank, and Ledger.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Runs history */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100">
          <h2 className="font-bold text-base text-slate-900">Reconciliation Run Audit History</h2>
          <p className="text-xs text-slate-500">Summary of executed runs</p>
        </div>
        <div className="divide-y divide-slate-100">
          {runs.map((r) => (
            <div key={r.id} className="p-4 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <span className="font-mono font-bold text-slate-900">{r.run_reference}</span>
                <div className="text-slate-400">Executed {new Date(r.created_at).toLocaleString()}</div>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-slate-600">Switch: {r.total_switch_records} txs</span>
                <span className="text-slate-600">Bank: {r.total_bank_records} txs</span>
                <span className="font-bold text-emerald-600">{r.total_matched} Matched</span>
                <span className="font-bold text-rose-600">{r.total_exceptions} Exceptions</span>
                <StatusBadge status={r.status} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resolution Modal */}
      {selectedException && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Resolve Reconciliation Discrepancy</h3>
            <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200 leading-relaxed">
              <strong>Discrepancy:</strong> {selectedException.explanation}
            </p>

            <form onSubmit={handleResolveException} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Investigation & Resolution Notes
                </label>
                <textarea
                  rows={3}
                  required
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedException(null)}
                  className="flex-1 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resolving}
                  className="flex-1 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold disabled:opacity-50"
                >
                  {resolving ? 'Recording...' : 'Mark Resolved'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
