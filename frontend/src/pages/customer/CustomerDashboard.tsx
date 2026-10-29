import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreditCard, ArrowRightLeft, ShieldCheck, Plus, History, ExternalLink } from 'lucide-react';
import { api } from '../../services/api';
import { SimulatedAccount, PaymentInstrument, Payment } from '../../types';
import { MetricCard } from '../../components/MetricCard';
import { StatusBadge } from '../../components/StatusBadge';
import { ReceiptModal } from '../../components/ReceiptModal';

export const CustomerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<SimulatedAccount[]>([]);
  const [instruments, setInstruments] = useState<PaymentInstrument[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState<Payment | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [accRes, instRes, payRes] = await Promise.all([
          api.getAccounts(),
          api.getInstruments(),
          api.getPayments('limit=10'),
        ]);
        setAccounts(accRes);
        setInstruments(instRes);
        setPayments(payRes);
      } catch (err) {
        console.error('Failed to load customer dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalBalancePaise = accounts.reduce((acc, curr) => acc + curr.available_balance_paise, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading accounts and balances...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Customer Portal</h1>
          <p className="text-xs text-slate-500">Manage simulated bank accounts, test instruments, and transactions</p>
        </div>
        <button
          onClick={() => navigate('/customer/pay')}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-semibold shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Payment</span>
        </button>
      </div>

      {/* Financial Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Total Available Balance"
          value={`₹${(totalBalancePaise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtitle="Across all simulated bank accounts"
          icon={<CreditCard className="w-5 h-5 text-teal-600" />}
          badge="Live Ledger Balance"
        />
        <MetricCard
          title="Registered Test Instruments"
          value={instruments.length}
          subtitle="UPI VPAs & Tokenized Cards"
          icon={<ShieldCheck className="w-5 h-5 text-indigo-600" />}
        />
        <MetricCard
          title="Recent Payments"
          value={payments.length}
          subtitle="Simulated transactions"
          icon={<History className="w-5 h-5 text-slate-600" />}
        />
      </div>

      {/* Simulated Bank Accounts */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base text-slate-900">Simulated Bank Accounts</h2>
            <p className="text-xs text-slate-500">Holdings with simulated clearing houses</p>
          </div>
        </div>
        <div className="divide-y divide-slate-100">
          {accounts.map((acc) => (
            <div key={acc.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-slate-900 text-sm">{acc.bank.name}</span>
                  <span className="text-[10px] bg-slate-100 text-slate-600 font-mono px-2 py-0.5 rounded">
                    {acc.bank.code}
                  </span>
                </div>
                <div className="text-xs text-slate-500 font-mono">A/C: {acc.account_number} • {acc.account_type}</div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-slate-900">
                  ₹{(acc.available_balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <div className="text-[11px] text-slate-400">Available to Spend</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Saved Instruments */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100">
          <h2 className="font-bold text-base text-slate-900">Test Payment Instruments</h2>
          <p className="text-xs text-slate-500">Demo UPI VPAs and tokenized mock cards</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 p-5">
          {instruments.map((inst) => (
            <div key={inst.id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-teal-700 uppercase">{inst.instrument_type}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              </div>
              <div className="font-mono text-sm font-bold text-slate-900">{inst.masked_identifier}</div>
              <div className="text-[10px] text-slate-400 font-mono truncate">Token: {inst.token_ref}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Payments Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base text-slate-900">Recent Transactions</h2>
            <p className="text-xs text-slate-500">Latest activity from your customer account</p>
          </div>
          <button
            onClick={() => navigate('/customer/transactions')}
            className="text-xs font-semibold text-teal-600 hover:text-teal-700"
          >
            View All
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Merchant</th>
                <th className="px-5 py-3">Method</th>
                <th className="px-5 py-3">Amount</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Bank Ref</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {payments.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3.5 text-slate-600">{new Date(p.created_at).toLocaleTimeString()}</td>
                  <td className="px-5 py-3.5 font-semibold text-slate-900">{p.merchant_name || p.merchant_id}</td>
                  <td className="px-5 py-3.5 font-medium text-slate-700">{p.payment_method}</td>
                  <td className="px-5 py-3.5 font-bold text-slate-900">
                    ₹{(p.amount_paise / 100).toFixed(2)}
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-5 py-3.5 font-mono text-[11px] text-slate-500">
                    {p.bank_reference || 'N/A'}
                  </td>
                  <td className="px-5 py-3.5 text-right space-x-2">
                    <button
                      onClick={() => navigate(`/customer/payments/${p.id}`)}
                      className="text-teal-600 hover:text-teal-700 font-semibold"
                    >
                      Detail
                    </button>
                    {p.status === 'SUCCEEDED' && (
                      <button
                        onClick={() => setSelectedReceipt(p)}
                        className="text-slate-600 hover:text-slate-900 font-medium"
                      >
                        Receipt
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedReceipt && (
        <ReceiptModal payment={selectedReceipt} onClose={() => setSelectedReceipt(null)} />
      )}
    </div>
  );
};
