import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRightLeft, ShieldCheck, Scale, Cpu, CreditCard, ChevronRight, Layers, Lock } from 'lucide-react';

export const IntroPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-6xl mx-auto px-4 py-10 space-y-12">
      {/* Hero section */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-800 text-xs font-semibold uppercase tracking-wider">
          <Cpu className="w-3.5 h-3.5" />
          <span>LNTFINTECH Academic Project Submission</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Secure Payment Switch & <span className="text-teal-600">Merchant Acquiring</span> Simulator
        </h1>
        <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
          An educational platform simulating how digital payments (UPI, Tokenized Card, NEFT, and RTGS) are routed through a high-throughput switch, authorized by simulated bank cores, recorded in balanced double-entry accounting ledgers, settled to merchants, and verified through three-way reconciliation.
        </p>

        <div className="pt-4 flex items-center justify-center space-x-4">
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-semibold text-sm shadow-md transition-all flex items-center space-x-2"
          >
            <span>Launch Simulation Demo</span>
            <ChevronRight className="w-4 h-4" />
          </button>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-xl font-semibold text-sm shadow-sm transition-all"
          >
            OpenAPI Docs
          </a>
        </div>
      </div>

      {/* 4 Pillars Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <ArrowRightLeft className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-base">Multi-Method Switch</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Simplified UPI VPAs, Card token authorization holds & captures, NEFT asynchronous batch queuing, and RTGS high-value routing.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-base">Double-Entry Ledger</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Immutable journal entries with integer paise arithmetic. Strict balancing invariant ensures Total Debits equal Total Credits.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Layers className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-base">Merchant Acquiring</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Merchant onboarding, snapshot fee deductions (basis points and fixed paise), cutoff batch execution, and payout retry mechanisms.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <Scale className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-base">3-Way Reconciliation</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Automated comparison between Switch transaction logs, independent simulated Bank Core records, and double-entry Ledger postings.
          </p>
        </div>
      </div>

      {/* Architecture & Simulation Scenarios Overview */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm space-y-6">
        <h2 className="text-xl font-bold text-slate-900">13 Built-in Failure & Resilience Scenarios</h2>
        <p className="text-sm text-slate-600">
          The admin simulation console allows live testing of edge cases without mocking frontend results:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          {[
            '1. SUCCESS (Normal execution)',
            '2. INSUFFICIENT_FUNDS (Zero-debit decline)',
            '3. INVALID_DEMO_AUTH (PIN / OTP error)',
            '4. BANK_UNAVAILABLE (HTTP 503 gateway outage)',
            '5. SLOW_RESPONSE (800ms latency simulation)',
            '6. TIMEOUT_BEFORE_PROCESSING (Switch timeout)',
            '7. TIMEOUT_AFTER_BANK_SUCCESS (Pending resolution)',
            '8. DUPLICATE_EVENT (Idempotency enforcement)',
            '9. RISK_REVIEW (Manual admin compliance review)',
            '10. RECONCILIATION_MISSING_RECORD (Dropped bank entry)',
            '11. RECONCILIATION_AMOUNT_MISMATCH (Discrepancy test)',
            '12. RECONCILIATION_STATUS_MISMATCH (Discrepancy test)',
            '13. SETTLEMENT_PAYOUT_FAILURE (Payout retry test)',
          ].map((s, idx) => (
            <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-100 font-mono text-slate-800">
              {s}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
