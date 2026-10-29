import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CreditCard,
  ArrowRightLeft,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Shield,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { api } from '../../services/api';
import { Merchant, PaymentInstrument, PaymentMethod, Payment } from '../../types';
import { ReceiptModal } from '../../components/ReceiptModal';

export const NewPaymentPage: React.FC = () => {
  const navigate = useNavigate();
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [instruments, setInstruments] = useState<PaymentInstrument[]>([]);
  const [loading, setLoading] = useState(true);

  // Form state
  const [selectedMerchantId, setSelectedMerchantId] = useState('');
  const [method, setMethod] = useState<PaymentMethod>('UPI');
  const [amountInr, setAmountInr] = useState('250.00');
  const [instrumentRef, setInstrumentRef] = useState('');
  const [orderRef, setOrderRef] = useState(`ORD-${Math.floor(1000 + Math.random() * 9000)}`);
  const [idempotencyKey, setIdempotencyKey] = useState(`idemp_${Math.random().toString(36).substring(2, 12)}`);
  const [demoAuth, setDemoAuth] = useState('PIN_1234');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultPayment, setResultPayment] = useState<Payment | null>(null);
  const [showReceipt, setShowReceipt] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const [mRes, instRes] = await Promise.all([
          api.getMerchants('APPROVED'),
          api.getInstruments(),
        ]);
        setMerchants(mRes);
        if (mRes.length > 0) setSelectedMerchantId(mRes[0].id);
        setInstruments(instRes);
        if (instRes.length > 0) setInstrumentRef(instRes[0].token_ref);
      } catch (err) {
        console.error('Failed to load form dependencies:', err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const regenerateIdempotency = () => {
    setIdempotencyKey(`idemp_${Math.random().toString(36).substring(2, 12)}`);
  };

  const selectedMerchant = merchants.find((m) => m.id === selectedMerchantId);
  const amountPaise = Math.round((parseFloat(amountInr) || 0) * 100);

  // Calculated fee preview
  let feePaisePreview = 0;
  if (selectedMerchant && amountPaise > 0) {
    const bps = selectedMerchant.fee_percentage_bps || 0;
    const flat = selectedMerchant.fee_flat_paise || 0;
    feePaisePreview = Math.round((amountPaise * bps) / 10000) + flat;
  }
  const netPaisePreview = Math.max(0, amountPaise - feePaisePreview);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    setResultPayment(null);

    try {
      const payload = {
        merchant_id: selectedMerchantId,
        payment_method: method,
        amount_paise: amountPaise,
        currency: 'INR',
        instrument_ref: instrumentRef || 'demo@simulator',
        merchant_order_ref: orderRef,
        idempotency_key: idempotencyKey,
        demo_auth_token: demoAuth,
      };

      const res = await api.initiatePayment(payload);
      setResultPayment(res);
      if (res.status === 'SUCCEEDED') {
        setShowReceipt(true);
      }
    } catch (err: any) {
      setError(err.message || 'Payment initiation failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading payment switch options...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Initiate Payment</h1>
        <p className="text-xs text-slate-500">Route a test payment through the simulated multi-method switch</p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-700 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold">Transaction Failed / Rejected</span>
            <p>{error}</p>
          </div>
        </div>
      )}

      {resultPayment && (
        <div
          className={`p-5 rounded-2xl border ${
            resultPayment.status === 'SUCCEEDED'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : resultPayment.status === 'PENDING'
              ? 'bg-amber-50 border-amber-200 text-amber-900'
              : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-bold text-sm">Status: {resultPayment.status}</span>
            </div>
            <button
              onClick={() => navigate(`/customer/payments/${resultPayment.id}`)}
              className="text-xs font-semibold underline"
            >
              View Full Switch Trace
            </button>
          </div>
          <div className="mt-2 text-xs font-mono space-y-1">
            <div>Bank Ref: {resultPayment.bank_reference || 'N/A'}</div>
            {resultPayment.error_message && <div>Message: {resultPayment.error_message}</div>}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6">
        {/* Merchant selection */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">Approved Merchant</label>
          <select
            value={selectedMerchantId}
            onChange={(e) => setSelectedMerchantId(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {merchants.map((m) => (
              <option key={m.id} value={m.id}>
                {m.business_name} (Fee: {(m.fee_percentage_bps / 100).toFixed(2)}% + ₹{(m.fee_flat_paise / 100).toFixed(2)})
              </option>
            ))}
          </select>
        </div>

        {/* Method selection */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">Payment Method</label>
          <div className="grid grid-cols-4 gap-2">
            {(['UPI', 'CARD', 'NEFT', 'RTGS'] as PaymentMethod[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMethod(m)}
                className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
                  method === m
                    ? 'border-teal-500 bg-teal-50 text-teal-900 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 text-slate-600 bg-slate-50'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        {/* Amount */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">Amount (INR)</label>
          <div className="relative">
            <span className="absolute left-3.5 top-2.5 font-bold text-slate-400">₹</span>
            <input
              type="number"
              step="0.01"
              min="1"
              required
              value={amountInr}
              onChange={(e) => setAmountInr(e.target.value)}
              className="w-full pl-8 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
          {method === 'RTGS' && parseFloat(amountInr) < 2000 && (
            <p className="text-[11px] text-amber-600 mt-1">
              Note: RTGS in this simulator requires minimum ₹2,000.00 for gross settlement.
            </p>
          )}
        </div>

        {/* Instrument selection */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">Simulated Payment Instrument</label>
          <select
            value={instrumentRef}
            onChange={(e) => setInstrumentRef(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {instruments.map((inst) => (
              <option key={inst.id} value={inst.token_ref}>
                {inst.instrument_type}: {inst.masked_identifier}
              </option>
            ))}
            <option value="custom_vpa@okhdfcbank">Custom VPA (custom_vpa@okhdfcbank)</option>
          </select>
        </div>

        {/* Demo Authentication Challenge */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Simulated Auth Challenge (MPIN / 3DS)
          </label>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => setDemoAuth('PIN_1234')}
              className={`p-2 rounded-xl border text-left transition-all ${
                demoAuth === 'PIN_1234'
                  ? 'border-emerald-500 bg-emerald-50 text-emerald-900 font-semibold'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              Valid Auth (PIN_1234)
            </button>
            <button
              type="button"
              onClick={() => setDemoAuth('PIN_WRONG')}
              className={`p-2 rounded-xl border text-left transition-all ${
                demoAuth === 'PIN_WRONG'
                  ? 'border-rose-500 bg-rose-50 text-rose-900 font-semibold'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              Invalid Auth (PIN_WRONG)
            </button>
          </div>
        </div>

        {/* Idempotency Key */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-semibold text-slate-700">Idempotency Key</label>
            <button
              type="button"
              onClick={regenerateIdempotency}
              className="text-[11px] text-teal-600 hover:text-teal-700 font-semibold flex items-center space-x-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Regenerate Key</span>
            </button>
          </div>
          <input
            type="text"
            required
            value={idempotencyKey}
            onChange={(e) => setIdempotencyKey(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>

        {/* Fee breakdown preview */}
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
          <div className="flex justify-between text-slate-600">
            <span>Customer Debit:</span>
            <span className="font-semibold text-slate-900">₹{(amountPaise / 100).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-slate-600">
            <span>Simulated Switch Fee:</span>
            <span className="font-semibold text-slate-900">₹{(feePaisePreview / 100).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-slate-800 font-bold border-t border-slate-200 pt-2">
            <span>Net Merchant Proceeds:</span>
            <span className="text-teal-700">₹{(netPaisePreview / 100).toFixed(2)}</span>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-semibold text-sm shadow-md transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <span>{submitting ? 'Routing Through Switch...' : `Pay ₹${(amountPaise / 100).toFixed(2)}`}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {showReceipt && resultPayment && (
        <ReceiptModal payment={resultPayment} onClose={() => setShowReceipt(false)} />
      )}
    </div>
  );
};
