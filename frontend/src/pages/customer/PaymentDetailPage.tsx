import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Printer, Shield, CheckCircle2, Clock, AlertTriangle, FileText } from 'lucide-react';
import { api } from '../../services/api';
import { Payment } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';
import { ReceiptModal } from '../../components/ReceiptModal';

export const PaymentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);
  const [showReceipt, setShowReceipt] = useState(false);

  useEffect(() => {
    async function load() {
      if (!id) return;
      try {
        const res = await api.getPaymentDetails(id);
        setPayment(res);
      } catch (err) {
        console.error('Error loading payment details:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleResolve = async () => {
    if (!id) return;
    setResolving(true);
    try {
      const res = await api.resolvePaymentStatus(id);
      setPayment(res);
    } catch (err) {
      console.error('Failed to resolve payment:', err);
    } finally {
      setResolving(false);
    }
  };

  if (loading || !payment) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading switch trace...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>
        <div className="flex items-center space-x-2">
          {payment.status === 'PENDING' && (
            <button
              onClick={handleResolve}
              disabled={resolving}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${resolving ? 'animate-spin' : ''}`} />
              <span>Poll / Resolve Pending Bank Outcome</span>
            </button>
          )}
          {payment.status === 'SUCCEEDED' && (
            <button
              onClick={() => setShowReceipt(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>View Receipt</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Payment Card */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <h1 className="text-xl font-extrabold text-slate-900">Payment {payment.id.slice(0, 8).toUpperCase()}</h1>
              <StatusBadge status={payment.status} />
            </div>
            <div className="text-xs font-mono text-slate-400">ID: {payment.id}</div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-black text-slate-900">
              ₹{(payment.amount_paise / 100).toFixed(2)}
            </div>
            <div className="text-xs text-slate-500">Method: {payment.payment_method}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-slate-50/50 border-b border-slate-100 text-xs">
          <div>
            <span className="text-slate-400 block font-medium">Merchant</span>
            <span className="font-bold text-slate-900">{payment.merchant_name || payment.merchant_id}</span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Bank Reference</span>
            <span className="font-mono font-bold text-slate-800">{payment.bank_reference || 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Fee Deducted</span>
            <span className="font-bold text-slate-800">
              ₹{(payment.calculated_fee_paise / 100).toFixed(2)} ({(payment.fee_bps_snapshot / 100).toFixed(2)}% + ₹{(payment.fee_flat_paise_snapshot / 100).toFixed(2)})
            </span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Net Settlement Amount</span>
            <span className="font-bold text-teal-700">₹{(payment.net_merchant_paise / 100).toFixed(2)}</span>
          </div>
        </div>

        {payment.error_message && (
          <div className="p-4 bg-amber-50 border-b border-amber-200 text-xs text-amber-900 flex items-start space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600" />
            <div>
              <span className="font-bold">Error/Exception Note: </span>
              <span>{payment.error_message}</span>
            </div>
          </div>
        )}

        {/* Timeline Events */}
        <div className="p-6">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center space-x-1.5">
            <Clock className="w-4 h-4" />
            <span>Switch Processing Event Timeline</span>
          </h3>

          <div className="space-y-4">
            {payment.events && payment.events.length > 0 ? (
              payment.events.map((ev, idx) => (
                <div key={ev.id} className="relative pl-6 border-l-2 border-teal-500/30 pb-2 last:pb-0">
                  <div className="absolute -left-1.5 top-0 w-3 h-3 rounded-full bg-teal-500 ring-4 ring-white" />
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-900">{ev.event_type}</span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {new Date(ev.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-slate-600 mt-0.5">
                    {ev.from_status && <span className="font-mono text-slate-400">{ev.from_status} →</span>}
                    <span className="font-semibold font-mono text-slate-800">{ev.to_status}</span>
                  </div>
                  {ev.details && <p className="text-xs text-slate-500 mt-1 font-mono">{ev.details}</p>}
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400">No events recorded.</p>
            )}
          </div>
        </div>
      </div>

      {showReceipt && <ReceiptModal payment={payment} onClose={() => setShowReceipt(false)} />}
    </div>
  );
};
