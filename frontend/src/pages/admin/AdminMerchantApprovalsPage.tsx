import React, { useEffect, useState } from 'react';
import { Building2, Check, X, Ban, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { Merchant } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

export const AdminMerchantApprovalsPage: React.FC = () => {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewingId, setReviewingId] = useState<string | null>(null);

  const loadMerchants = async () => {
    try {
      const res = await api.getMerchants();
      setMerchants(res);
    } catch (err) {
      console.error('Failed to load merchants:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMerchants();
  }, []);

  const handleReview = async (id: string, status: 'APPROVED' | 'REJECTED' | 'SUSPENDED') => {
    setReviewingId(id);
    try {
      await api.reviewMerchant(id, {
        status,
        rejection_reason: status === 'REJECTED' ? 'Incomplete KYC documentation in academic simulation' : undefined,
      });
      await loadMerchants();
    } catch (err) {
      console.error('Failed to review merchant:', err);
    } finally {
      setReviewingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading merchant records...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Merchant Acquiring Approvals</h1>
        <p className="text-xs text-slate-500">Review onboarding applications, activate routes, or suspend accounts</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Business Name</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3">Contact Email</th>
                <th className="px-5 py-3">Settlement A/C</th>
                <th className="px-5 py-3">Fee Config</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {merchants.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3.5 font-bold text-slate-900">{m.business_name}</td>
                  <td className="px-5 py-3.5 text-slate-600">{m.business_category}</td>
                  <td className="px-5 py-3.5 font-mono text-slate-500">{m.contact_email}</td>
                  <td className="px-5 py-3.5 font-mono text-slate-600">{m.settlement_account_ref}</td>
                  <td className="px-5 py-3.5 text-slate-700 font-medium">
                    {(m.fee_percentage_bps / 100).toFixed(2)}% + ₹{(m.fee_flat_paise / 100).toFixed(2)}
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={m.status} />
                  </td>
                  <td className="px-5 py-3.5 text-right space-x-2">
                    {m.status !== 'APPROVED' && (
                      <button
                        onClick={() => handleReview(m.id, 'APPROVED')}
                        disabled={reviewingId === m.id}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold"
                      >
                        Approve
                      </button>
                    )}
                    {m.status === 'APPROVED' && (
                      <button
                        onClick={() => handleReview(m.id, 'SUSPENDED')}
                        disabled={reviewingId === m.id}
                        className="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold"
                      >
                        Suspend
                      </button>
                    )}
                    {m.status === 'PENDING' && (
                      <button
                        onClick={() => handleReview(m.id, 'REJECTED')}
                        disabled={reviewingId === m.id}
                        className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold"
                      >
                        Reject
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
