import React, { useEffect, useState } from 'react';
import { ShieldAlert, Plus, Check, X, Clock, AlertTriangle } from 'lucide-react';
import { api } from '../../services/api';
import { RiskRule, RiskDecision } from '../../types';

export const AdminRiskPage: React.FC = () => {
  const [rules, setRules] = useState<RiskRule[]>([]);
  const [reviewQueue, setReviewQueue] = useState<RiskDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  // New Rule form
  const [showAddModal, setShowAddModal] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [ruleDesc, setRuleDesc] = useState('');
  const [ruleType, setRuleType] = useState('MAX_AMOUNT');
  const [threshold, setThreshold] = useState('5000000');
  const [windowSec, setWindowSec] = useState('300');
  const [action, setAction] = useState<'ALLOW' | 'DECLINE' | 'REVIEW'>('REVIEW');

  const loadData = async () => {
    try {
      const [rRes, qRes] = await Promise.all([
        api.getRiskRules(),
        api.getReviewQueue(),
      ]);
      setRules(rRes);
      setReviewQueue(qRes);
    } catch (err) {
      console.error('Failed to load risk data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleResolve = async (paymentId: string, resolutionAction: 'APPROVE' | 'DECLINE') => {
    setResolvingId(paymentId);
    try {
      await api.resolveRiskReview(paymentId, {
        action: resolutionAction,
        notes: `Administrative manual review action: ${resolutionAction}`,
      });
      await loadData();
    } catch (err) {
      console.error('Failed to resolve risk review:', err);
    } finally {
      setResolvingId(null);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createRiskRule({
        name: ruleName,
        description: ruleDesc,
        rule_type: ruleType,
        threshold_value: parseInt(threshold),
        window_seconds: parseInt(windowSec),
        action,
        is_active: true,
      });
      setShowAddModal(false);
      setRuleName('');
      setRuleDesc('');
      await loadData();
    } catch (err) {
      console.error('Failed to create rule:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading risk rules...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Risk Rules & Compliance</h1>
          <p className="text-xs text-slate-500">Configurable risk boundaries and manual review queue</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Add Risk Rule</span>
        </button>
      </div>

      {/* Review Queue */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base text-slate-900">Flagged Review Queue</h2>
            <p className="text-xs text-slate-500">Transactions paused pending compliance review</p>
          </div>
          <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full">
            {reviewQueue.length} Pending Actions
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {reviewQueue.map((item) => (
            <div key={item.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-xs text-slate-900">Payment #{item.payment_id.slice(0, 8)}</span>
                  <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-2 py-0.5 rounded">
                    {item.action}
                  </span>
                </div>
                <p className="text-xs text-slate-600">{item.reason}</p>
                <div className="text-[11px] text-slate-400 font-mono">
                  Flagged {new Date(item.created_at).toLocaleString()}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleResolve(item.payment_id, 'APPROVE')}
                  disabled={resolvingId === item.payment_id}
                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center space-x-1"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve & Settle</span>
                </button>
                <button
                  onClick={() => handleResolve(item.payment_id, 'DECLINE')}
                  disabled={resolvingId === item.payment_id}
                  className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center space-x-1"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Decline & Release Hold</span>
                </button>
              </div>
            </div>
          ))}
          {reviewQueue.length === 0 && (
            <div className="p-8 text-center text-xs text-slate-400">
              Review queue is empty. No flagged payments awaiting review.
            </div>
          )}
        </div>
      </div>

      {/* Risk Rules List */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100">
          <h2 className="font-bold text-base text-slate-900">Active Risk Check Rules</h2>
          <p className="text-xs text-slate-500">Evaluated on payment initiation before switch routing</p>
        </div>

        <div className="divide-y divide-slate-100">
          {rules.map((rule) => (
            <div key={rule.id} className="p-4 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <div className="font-bold text-slate-900">{rule.name}</div>
                <p className="text-slate-500">{rule.description}</p>
                <div className="text-[11px] text-slate-400 font-mono">
                  Type: {rule.rule_type} • Threshold: {rule.threshold_value} • Window: {rule.window_seconds}s
                </div>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full font-bold text-[10px] ${
                  rule.action === 'DECLINE'
                    ? 'bg-rose-100 text-rose-800'
                    : rule.action === 'REVIEW'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                ACTION: {rule.action}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Add Rule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Add New Risk Rule</h3>
            <form onSubmit={handleCreateRule} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  placeholder="e.g. Velocity Alert Rule"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <input
                  type="text"
                  required
                  value={ruleDesc}
                  onChange={(e) => setRuleDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  placeholder="e.g. Reject more than 5 payments in 60s"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Rule Type</label>
                <select
                  value={ruleType}
                  onChange={(e) => setRuleType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                >
                  <option value="MAX_AMOUNT">MAX_AMOUNT (Threshold in Paise)</option>
                  <option value="VELOCITY_WINDOW">VELOCITY_WINDOW (Max attempts per window)</option>
                  <option value="REPEATED_MERCHANT">REPEATED_MERCHANT (Repeated merchant txs)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Threshold</label>
                  <input
                    type="number"
                    required
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Window (Seconds)</label>
                  <input
                    type="number"
                    required
                    value={windowSec}
                    onChange={(e) => setWindowSec(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Action</label>
                <select
                  value={action}
                  onChange={(e) => setAction(e.target.value as any)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                >
                  <option value="REVIEW">REVIEW (Hold for Admin Approval)</option>
                  <option value="DECLINE">DECLINE (Instant Rejection)</option>
                </select>
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-semibold"
                >
                  Save Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
