import React, { useEffect, useState } from 'react';
import { FileText, ShieldCheck, RefreshCw, Key } from 'lucide-react';
import { api } from '../../services/api';
import { AuditLog } from '../../types';

export const AdminAuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [integrity, setIntegrity] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [logsRes, intRes] = await Promise.all([
        api.getAuditLogs(),
        api.getLedgerIntegrity(),
      ]);
      setLogs(logsRes);
      setIntegrity(intRes);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading immutable audit log...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Audit Trail & Ledger Integrity</h1>
          <p className="text-xs text-slate-500">Append-only security log records and double-entry accounting proof</p>
        </div>
        <button
          onClick={loadData}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Ledger Integrity Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-3">
          <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-sm text-slate-900">Double-Entry Ledger Balancing Proof</h2>
            <p className="text-xs text-slate-500">Mathematical proof that Σ(Debits) - Σ(Credits) = 0 across all currencies</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl text-xs font-mono">
          <div>
            <span className="text-slate-400 block font-sans">Total System Debits</span>
            <span className="font-bold text-slate-900">
              ₹{(integrity?.total_debits_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block font-sans">Total System Credits</span>
            <span className="font-bold text-slate-900">
              ₹{(integrity?.total_credits_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block font-sans">Discrepancy Variance</span>
            <span className="font-bold text-emerald-600">
              ₹{(integrity?.difference_paise / 100).toFixed(2)}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block font-sans">Accounting Integrity</span>
            <span className="font-bold text-emerald-700 font-sans">
              {integrity?.is_balanced ? 'VERIFIED BALANCED' : 'IMBALANCE DETECTED'}
            </span>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100">
          <h2 className="font-bold text-base text-slate-900">System Security Audit Events</h2>
          <p className="text-xs text-slate-500">Traceable records with Correlation IDs and redacted secrets</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Timestamp (UTC)</th>
                <th className="px-5 py-3">Action</th>
                <th className="px-5 py-3">Entity</th>
                <th className="px-5 py-3">Correlation ID</th>
                <th className="px-5 py-3">Changes / Payload Summary</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {logs.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3 text-slate-500">{new Date(l.created_at).toISOString()}</td>
                  <td className="px-5 py-3 font-bold text-slate-900">{l.action}</td>
                  <td className="px-5 py-3 text-slate-600">
                    {l.entity_type} {l.entity_id ? `(#${l.entity_id.slice(0, 6)})` : ''}
                  </td>
                  <td className="px-5 py-3 text-teal-700 truncate max-w-[12rem]">{l.correlation_id || '—'}</td>
                  <td className="px-5 py-3 text-slate-600 truncate max-w-sm">{l.changes || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
