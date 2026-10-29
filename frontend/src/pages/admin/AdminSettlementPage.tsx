import React, { useEffect, useState } from 'react';
import { Layers, ArrowDownLeft, RefreshCw, AlertCircle, CheckCircle2, Play, ChevronDown, ChevronRight } from 'lucide-react';
import { api } from '../../services/api';
import { SettlementBatch, SettlementItem } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const AdminSettlementPage: React.FC = () => {
  const [preview, setPreview] = useState<any>(null);
  const [batches, setBatches] = useState<SettlementBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [expandedBatchId, setExpandedBatchId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [prevRes, batchRes] = await Promise.all([
        api.getSettlementPreview().catch(() => null),
        api.getSettlementBatches(),
      ]);
      setPreview(prevRes);
      setBatches(batchRes);
      if (batchRes.length > 0 && !expandedBatchId) {
        setExpandedBatchId(batchRes[0].id);
      }
    } catch (err) {
      console.error('Error loading settlement data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteBatch = async () => {
    setExecuting(true);
    setMsg(null);
    try {
      const batch = await api.createSettlementBatch();
      setMsg(`Settlement batch ${batch.batch_reference} created and processed!`);
      await loadData();
    } catch (err: any) {
      setMsg(`Execution failed: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleRetryPayout = async (itemId: string) => {
    setRetryingId(itemId);
    try {
      await api.retrySettlementPayout(itemId);
      setMsg(`Payout item retry succeeded! Ledger updated.`);
      await loadData();
    } catch (err: any) {
      setMsg(`Retry failed: ${err.message}`);
    } finally {
      setRetryingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading settlement engine...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Settlement Engine</h1>
          <p className="text-xs text-slate-500">Calculate net merchant proceeds, execute payouts, and resolve failed transfers</p>
        </div>
      </div>

      {msg && (
        <div className="p-4 bg-slate-900 text-teal-300 rounded-2xl text-xs font-mono flex items-center justify-between">
          <span>{msg}</span>
          <button onClick={() => setMsg(null)} className="text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Settlement Preview Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Current Settlement Preview</h2>
            <p className="text-xs text-slate-500">Unsettled captured transactions and refund adjustments ready for batch</p>
          </div>
          <button
            onClick={handleExecuteBatch}
            disabled={executing || !preview?.merchants?.length}
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold shadow-md transition-all disabled:opacity-40"
          >
            <Play className={`w-3.5 h-3.5 ${executing ? 'animate-spin' : ''}`} />
            <span>{executing ? 'Executing Batch...' : 'Execute Settlement Batch'}</span>
          </button>
        </div>

        {preview && preview.merchants?.length > 0 ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl text-xs">
              <div>
                <span className="text-slate-400 block font-medium">Eligible Gross Sales</span>
                <span className="text-base font-bold text-slate-900">
                  ₹{(preview.total_gross_paise / 100).toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Switch Fee Deductions</span>
                <span className="text-base font-bold text-indigo-700">
                  -₹{(preview.total_fee_paise / 100).toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Refund Adjustments</span>
                <span className="text-base font-bold text-rose-600">
                  -₹{(preview.total_refund_paise / 100).toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Total Net Payable</span>
                <span className="text-base font-black text-teal-700">
                  ₹{(preview.total_net_payable_paise / 100).toFixed(2)}
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-2">Merchant</th>
                    <th className="px-4 py-2">Txs</th>
                    <th className="px-4 py-2">Gross Sales</th>
                    <th className="px-4 py-2">Fees</th>
                    <th className="px-4 py-2">Refunds</th>
                    <th className="px-4 py-2">Net Payable</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {preview.merchants.map((m: any) => (
                    <tr key={m.merchant_id}>
                      <td className="px-4 py-2.5 font-bold text-slate-900">{m.merchant_name}</td>
                      <td className="px-4 py-2.5">{m.eligible_payment_count}</td>
                      <td className="px-4 py-2.5 font-medium">₹{(m.gross_amount_paise / 100).toFixed(2)}</td>
                      <td className="px-4 py-2.5 text-slate-500">₹{(m.fee_amount_paise / 100).toFixed(2)}</td>
                      <td className="px-4 py-2.5 text-rose-600">₹{(m.refund_amount_paise / 100).toFixed(2)}</td>
                      <td className="px-4 py-2.5 font-bold text-teal-700">₹{(m.net_payable_paise / 100).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center bg-slate-50 rounded-xl text-xs text-slate-400">
            No pending captured payments or refunds require settlement right now.
          </div>
        )}
      </div>

      {/* Historical Batches & Payout Retries */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100">
          <h2 className="font-bold text-base text-slate-900">Settlement Batches & Item Payouts</h2>
          <p className="text-xs text-slate-500">Inspect batch allocations and retry failed nodal payouts</p>
        </div>

        <div className="divide-y divide-slate-100">
          {batches.map((b) => (
            <div key={b.id} className="p-5 space-y-4">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpandedBatchId(expandedBatchId === b.id ? null : b.id)}
              >
                <div className="flex items-center space-x-3">
                  {expandedBatchId === b.id ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                  <div>
                    <span className="font-bold text-sm text-slate-900">{b.batch_reference}</span>
                    <span className="text-xs text-slate-400 font-mono ml-2">
                      {new Date(b.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-bold text-slate-900">
                    Net: ₹{(b.total_net_paise / 100).toFixed(2)}
                  </span>
                  <StatusBadge status={b.status} />
                </div>
              </div>

              {expandedBatchId === b.id && b.items && (
                <div className="pl-6 pt-2 border-t border-slate-100">
                  <table className="w-full text-left text-xs">
                    <thead className="text-slate-400 font-semibold uppercase">
                      <tr>
                        <th className="py-2">Merchant</th>
                        <th className="py-2">Payout Ref</th>
                        <th className="py-2">Net Payable</th>
                        <th className="py-2">Status</th>
                        <th className="py-2">Error / Details</th>
                        <th className="py-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {b.items.map((it) => (
                        <tr key={it.id}>
                          <td className="py-2.5 font-semibold text-slate-900">{it.merchant_name || it.merchant_id}</td>
                          <td className="py-2.5 font-mono text-[11px] text-slate-600">{it.payout_reference || 'N/A'}</td>
                          <td className="py-2.5 font-bold text-slate-900">₹{(it.net_payable_paise / 100).toFixed(2)}</td>
                          <td className="py-2.5">
                            <StatusBadge status={it.status} />
                          </td>
                          <td className="py-2.5 text-xs text-rose-600 max-w-xs truncate">
                            {it.last_error || 'Transfer confirmed'}
                          </td>
                          <td className="py-2.5 text-right">
                            {it.status === 'FAILED' && (
                              <button
                                onClick={() => handleRetryPayout(it.id)}
                                disabled={retryingId === it.id}
                                className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 rounded-lg text-xs font-bold"
                              >
                                {retryingId === it.id ? 'Retrying...' : 'Retry Payout'}
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
