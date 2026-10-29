import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRightLeft, Shield, Lock, Mail, ArrowRight, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { User } from '../../types';

interface Props {
  onLoginSuccess: (user: User) => void;
}

export const LoginPage: React.FC<Props> = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('admin@lntfintech.edu');
  const [password, setPassword] = useState('Admin@12345');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login({ email, password });
      localStorage.setItem('switch_token', res.access_token);
      onLoginSuccess(res.user);
      if (res.user.role === 'ADMIN') navigate('/admin');
      else if (res.user.role === 'MERCHANT') navigate('/merchant');
      else navigate('/customer');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden p-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center mx-auto text-teal-400 shadow-lg shadow-slate-900/10">
            <ArrowRightLeft className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Sign In to Simulator</h2>
          <p className="text-xs text-slate-500">Select a pre-seeded persona or enter your credentials</p>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 1-Click Persona selection */}
        <div className="space-y-2">
          <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            Quick Demo Persona
          </label>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => handleQuickLogin('admin@lntfintech.edu', 'Admin@12345')}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === 'admin@lntfintech.edu'
                  ? 'border-teal-500 bg-teal-50 text-teal-900 font-semibold'
                  : 'border-slate-200 hover:border-slate-300 bg-slate-50'
              }`}
            >
              <div className="font-bold">System Admin</div>
              <div className="text-[10px] text-slate-500 truncate">admin@lntfintech.edu</div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('merchant.acme@lntfintech.edu', 'Merchant@12345')}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === 'merchant.acme@lntfintech.edu'
                  ? 'border-teal-500 bg-teal-50 text-teal-900 font-semibold'
                  : 'border-slate-200 hover:border-slate-300 bg-slate-50'
              }`}
            >
              <div className="font-bold">Acme Merchant</div>
              <div className="text-[10px] text-slate-500 truncate">merchant.acme@...</div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('merchant.nova@lntfintech.edu', 'Merchant@12345')}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === 'merchant.nova@lntfintech.edu'
                  ? 'border-teal-500 bg-teal-50 text-teal-900 font-semibold'
                  : 'border-slate-200 hover:border-slate-300 bg-slate-50'
              }`}
            >
              <div className="font-bold">Nova Merchant</div>
              <div className="text-[10px] text-slate-500 truncate">merchant.nova@...</div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('customer1@lntfintech.edu', 'Customer@12345')}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === 'customer1@lntfintech.edu'
                  ? 'border-teal-500 bg-teal-50 text-teal-900 font-semibold'
                  : 'border-slate-200 hover:border-slate-300 bg-slate-50'
              }`}
            >
              <div className="font-bold">Rahul (Customer 1)</div>
              <div className="text-[10px] text-slate-500 truncate">customer1@...</div>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-semibold text-sm shadow-md transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-2 text-center text-xs text-slate-500 border-t border-slate-100">
          Academic submission project for <strong className="text-slate-700">LNTFINTECH</strong>.
        </div>
      </div>
    </div>
  );
};
