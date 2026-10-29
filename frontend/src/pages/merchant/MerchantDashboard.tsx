import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, DollarSign, ArrowDownLeft, RotateCcw, Search, Download, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { Payment, Merchant } from '../../types';
import { MetricCard } from '../../components/MetricCard';
import { StatusBadge } from '../../components/StatusBadge';

export const MerchantDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Refund Modal State
  const [refundPayment, setRefundPayment] = useState<Payment | null>(null);
  const [refundAmountInr, setRefundAmountInr] = useState('');
  const [refundReason, setRefundReason] = useState('Customer returned goods');
  const [refunding, setRefunding] = useState(false);
  const [refundError, setRefundError] = useState<string | null>(null);
  const [refundSuccess, setRefundSuccess] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [mRes, pRes] = await Promise.all([
        api.getMerchantProfile(),
        api.getPayments('limit=100'),
      ]);
      setMerchant(mRes);
      setPayments(pRes);
    } catch (err) {
      console.error('Failed to load merchant data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openRefundModal = (p: Payment) => {
    setRefundPayment(p);
    const availablePaise = p.amount_paise - p.total_refunded_paise;
    setRefundAmountInr((availablePaise / 100).toFixed(2));
    setRefundError(null);
    setRefundSuccess(null);
  };

  const handleRefundSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!refundPayment) return;
    setRefunding(true);
    setRefundError(null);

    const amountPaise = Math.round(parseFloat(refundAmountInr) * 100);

    try {
      await api.createRefund({
        payment_id: refundPayment.id,
        amount_paise: amountPaise,
        reason: refundReason,
        idempotency_key: `ref_${Math.random().toString(36).substring(2, 12)}`,
      });
      setRefundSuccess(`Refund of ₹${(amountPaise / 100).toFixed(2)} processed successfully!`);
      setTimeout(() => {
        setRefundPayment(null);
        loadData();
      }, 1200);
    } catch (err: any) {
      setRefundError(err.message || 'Refund failed.');
    } finally {
      setRefunding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading merchant portal...</div>
      </div>
    );
  }

  const succeededPayments = payments.filter((p) => p.status === 'SUCCEEDED');
  const totalVolumePaise = succeededPayments.reduce((acc, p) => acc + p.amount_paise, 0);
  const totalFeePaise = succeededPayments.reduce((acc, p) => acc + p.calculated_fee_paise, 0);
  const totalRefundedPaise = payments.reduce((acc, p) => acc + p.total_refunded_paise, 0);
  const netPayablePaise = totalVolumePaise - totalFeePaise - totalRefundedPaise;

  const filteredPayments = payments.filter((p) => {
    const term = searchTerm.toLowerCase();
    return (
      p.id.toLowerCase().includes(term) ||
      (p.merchant_order_ref && p.merchant_order_ref.toLowerCase().includes(term)) ||
      (p.bank_reference && p.bank_reference.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {merchant?.business_name || 'Merchant Dashboard'}
            </h1>
            {merchant && <StatusBadge status={merchant.status} />}
          </div>
          <p className="text-xs text-slate-500">
            Acquiring rate: {(merchant?.fee_percentage_bps || 0) / 100}% + ₹{((merchant?.fee_flat_paise || 0) / 100).toFixed(2)} flat • Settlement A/C: {merchant?.settlement_account_ref}
          </p>
        </div>

        <a
          href="/api/v1/reports/transactions/export"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center space-x-2 px-3.5 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <Download className="w-4 h-4 text-slate-500" />
          <span>Export CSV</span>
        </a>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Captured Volume"
          value={`₹${(totalVolumePaise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtitle={`${succeededPayments.length} successful payments`}
          icon={<DollarSign className="w-5 h-5 text-emerald-600" />}
        />
        <MetricCard
          title="Switch Fee Deductions"
          value={`₹${(totalFeePaise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtitle="Snapshot interchange & switch fee"
          icon={<Building2 className="w-5 h-5 text-indigo-600" />}
        />
        <MetricCard
          title="Total Refunds"
          value={`₹${(totalRefundedPaise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtitle="Processed reversals"
          icon={<RotateCcw className="w-5 h-5 text-rose-600" />}
        />
        <MetricCard
          title="Net Settlement Payable"
          value={`₹${(netPayablePaise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtitle="Eligible proceeds for batch"
          icon={<ArrowDownLeft className="w-5 h-5 text-teal-600" />}
          badge="Payable"
        />
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="font-bold text-base text-slate-900">Payments & Orders</h2>
            <p className="text-xs text-slate-500">Live transactions received by your merchant acquiring account</p>
          </div>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by ID, order or bank ref..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs w-64 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Order / ID</th>
                <th className="px-5 py-3">Method</th>
                <th className="px-5 py-3">Gross Amount</th>
                <th className="px-5 py-3">Fee</th>
                <th className="px-5 py-3">Net</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Refunded</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredPayments.map((p) => {
                const availableToRefund = p.amount_paise - p.total_refunded_paise;
                const canRefund = p.status === 'SUCCEEDED' && availableToRefund > 0;

                return (
                  <tr key={p.id} className="hover:bg-slate-50/50">
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900">{p.merchant_order_ref || 'Direct Pay'}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{p.id.slice(0, 8)}</div>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-slate-700">{p.payment_method}</td>
                    <td className="px-5 py-3.5 font-bold text-slate-900">₹{(p.amount_paise / 100).toFixed(2)}</td>
                    <td className="px-5 py-3.5 text-slate-600">₹{(p.calculated_fee_paise / 100).toFixed(2)}</td>
                    <td className="px-5 py-3.5 font-bold text-teal-700">₹{(p.net_merchant_paise / 100).toFixed(2)}</td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={p.status} />
                    </td>
                    <td className="px-5 py-3.5 text-slate-500">
                      {p.total_refunded_paise > 0 ? `₹${(p.total_refunded_paise / 100).toFixed(2)}` : '—'}
                    </td>
                    <td className="px-5 py-3.5 text-right space-x-2">
                      <button
                        onClick={() => navigate(`/customer/payments/${p.id}`)}
                        className="text-slate-600 hover:text-slate-900 font-semibold"
                      >
                        Detail
                      </button>
                      {canRefund && (
                        <button
                          onClick={() => openRefundModal(p)}
                          className="text-rose-600 hover:text-rose-700 font-semibold"
                        >
                          Refund
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Refund Modal */}
      {refundPayment && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Issue Refund</h3>
            <p className="text-xs text-slate-500">
              Refund payment #{refundPayment.id.slice(0, 8)} • Max available: ₹
              {((refundPayment.amount_paise - refundPayment.total_refunded_paise) / 100).toFixed(2)}
            </p>

            {refundError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
                {refundError}
              </div>
            )}
            {refundSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-700 flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>{refundSuccess}</span>
              </div>
            )}

            <form onSubmit={handleRefundSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Refund Amount (INR)</label>
                <input
                  type="number"
                  step="0.01"
                  min="1"
                  max={(refundPayment.amount_paise - refundPayment.total_refunded_paise) / 100}
                  required
                  value={refundAmountInr}
                  onChange={(e) => setRefundAmountInr(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Reason for Refund</label>
                <input
                  type="text"
                  required
                  value={refundReason}
                  onChange={(e) => setRefundReason(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setRefundPayment(null)}
                  className="flex-1 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={refunding}
                  className="flex-1 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-semibold disabled:opacity-50"
                >
                  {refunding ? 'Processing...' : 'Confirm Refund'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
