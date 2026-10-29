import React, { useEffect, useState } from 'react';
import { FileCheck2, ArrowDownLeft, Clock, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { SettlementItem } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const MerchantSettlementsPage: React.FC = () => {
  const [items, setItems] = useState<SettlementItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getMerchantSettlements();
        setItems(res);
      } catch (err) {
        console.error('Failed to load settlement items:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading settlement statements...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Settlement Statements</h1>
        <p className="text-xs text-slate-500">Historical payouts transferred to your nodal settlement account</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Payout Reference</th>
                <th className="px-5 py-3">Created (UTC)</th>
                <th className="px-5 py-3">Gross Sales</th>
                <th className="px-5 py-3">Fee Deductions</th>
                <th className="px-5 py-3">Refund Adjustments</th>
                <th className="px-5 py-3">Net Payout</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((it) => (
                <tr key={it.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3.5 font-mono font-bold text-slate-900">
                    {it.payout_reference || it.id.slice(0, 8)}
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">
                    {new Date(it.created_at).toLocaleDateString()} {new Date(it.created_at).toLocaleTimeString()}
                  </td>
                  <td className="px-5 py-3.5 font-semibold text-slate-900">
                    ₹{(it.gross_amount_paise / 100).toFixed(2)}
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">
                    -₹{(it.fee_amount_paise / 100).toFixed(2)}
                  </td>
                  <td className="px-5 py-3.5 text-rose-600">
                    {it.refund_amount_paise > 0 ? `-₹${(it.refund_amount_paise / 100).toFixed(2)}` : '₹0.00'}
                  </td>
                  <td className="px-5 py-3.5 font-bold text-teal-700 text-sm">
                    ₹{(it.net_payable_paise / 100).toFixed(2)}
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={it.status} />
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-400">
                    No settlement statements generated yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
