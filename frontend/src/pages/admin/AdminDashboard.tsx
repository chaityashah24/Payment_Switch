import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  CreditCard,
  Building2,
  Sliders,
  Scale,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { api } from '../../services/api';
import { DashboardMetrics } from '../../types';
import { MetricCard } from '../../components/MetricCard';

const COLORS = ['#0d9488', '#3b82f6', '#6366f1', '#f59e0b', '#ef4444'];

export const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [integrity, setIntegrity] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [mRes, intRes] = await Promise.all([
          api.getDashboardMetrics(),
          api.getLedgerIntegrity(),
        ]);
        setMetrics(mRes);
        setIntegrity(intRes);
      } catch (err) {
        console.error('Failed to load admin metrics:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading switch analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Operations Console</h1>
          <p className="text-xs text-slate-500">Global payment switch, acquiring, ledger & reconciliation telemetry</p>
        </div>
        <div className="flex items-center space-x-2">
          {integrity?.is_balanced && (
            <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-xl text-xs font-semibold border border-emerald-200">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Ledger Invariant: Balanced (0 Diff)</span>
            </div>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Captured Volume"
          value={metrics.total_volume_inr}
          subtitle={`${metrics.succeeded_count} of ${metrics.total_transactions} txs`}
          icon={<TrendingUp className="w-5 h-5 text-teal-600" />}
          badge={`${metrics.success_rate_percent}% Success`}
        />
        <MetricCard
          title="Switch Fee Revenue"
          value={metrics.total_fee_inr}
          subtitle="Net switch fee earnings"
          icon={<Building2 className="w-5 h-5 text-indigo-600" />}
        />
        <MetricCard
          title="Net Merchant Payable"
          value={metrics.net_payable_inr}
          subtitle="Total clearing liability"
          icon={<CreditCard className="w-5 h-5 text-emerald-600" />}
        />
        <MetricCard
          title="Reconciliation Status"
          value={integrity?.is_balanced ? 'Balanced' : 'Discrepancy'}
          subtitle={`₹${(integrity?.total_debits_paise / 100 || 0).toLocaleString()} debit/credit`}
          icon={<Scale className="w-5 h-5 text-amber-600" />}
        />
      </div>

      {/* Quick Action Hub */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          onClick={() => navigate('/admin/scenarios')}
          className="bg-slate-900 text-white rounded-2xl p-6 cursor-pointer hover:bg-slate-800 transition-all shadow-md group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-amber-500/20 text-amber-400 rounded-xl">
              <Sliders className="w-6 h-6" />
            </div>
            <ArrowRight className="w-5 h-5 text-slate-400 group-hover:translate-x-1 transition-transform" />
          </div>
          <h3 className="font-bold text-lg">Simulation Console</h3>
          <p className="text-xs text-slate-400 mt-1">
            Trigger 13 failure scenarios: downtime, timeouts, missing records, insufficient funds, etc.
          </p>
        </div>

        <div
          onClick={() => navigate('/admin/settlements')}
          className="bg-white rounded-2xl p-6 border border-slate-200 cursor-pointer hover:border-slate-300 shadow-sm transition-all group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
              <Layers className="w-6 h-6" />
            </div>
            <ArrowRight className="w-5 h-5 text-slate-400 group-hover:translate-x-1 transition-transform" />
          </div>
          <h3 className="font-bold text-lg text-slate-900">Settlement Engine</h3>
          <p className="text-xs text-slate-500 mt-1">
            Preview merchant net amounts, execute batch payouts, and retry failed bank transfers.
          </p>
        </div>

        <div
          onClick={() => navigate('/admin/reconciliation')}
          className="bg-white rounded-2xl p-6 border border-slate-200 cursor-pointer hover:border-slate-300 shadow-sm transition-all group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
              <Scale className="w-6 h-6" />
            </div>
            <ArrowRight className="w-5 h-5 text-slate-400 group-hover:translate-x-1 transition-transform" />
          </div>
          <h3 className="font-bold text-lg text-slate-900">3-Way Reconciliation</h3>
          <p className="text-xs text-slate-500 mt-1">
            Compare Switch records vs Bank records vs Ledger lines. Investigate and resolve exceptions.
          </p>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-bold text-sm text-slate-900 mb-4">Payment Method Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.method_distribution}>
                <XAxis dataKey="method" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="#0d9488" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-bold text-sm text-slate-900 mb-4">Transaction Outcomes</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.status_distribution}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(entry) => `${entry.status}: ${entry.count}`}
                >
                  {metrics.status_distribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
