import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, UserCheck, LogOut, ArrowRightLeft, BookOpen } from 'lucide-react';
import { User } from '../types';
import { api } from '../services/api';

interface Props {
  user: User | null;
  onUserSwitch: (user: User) => void;
}

export const Navbar: React.FC<Props> = ({ user, onUserSwitch }) => {
  const navigate = useNavigate();

  const handleDemoSwitch = async (email: string, pass: string) => {
    try {
      const res = await api.login({ email, password: pass });
      localStorage.setItem('switch_token', res.access_token);
      onUserSwitch(res.user);
      if (res.user.role === 'ADMIN') navigate('/admin');
      else if (res.user.role === 'MERCHANT') navigate('/merchant');
      else navigate('/customer');
    } catch (err) {
      console.error('Demo login switch error:', err);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (e) {
      // Ignore
    }
    localStorage.removeItem('switch_token');
    window.location.href = '/login';
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-9 h-9 bg-teal-500 rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/20">
            <ArrowRightLeft className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base tracking-tight text-white">PaymentSwitch</span>
              <span className="text-[10px] bg-teal-500/20 text-teal-300 font-semibold px-2 py-0.5 rounded-full border border-teal-500/30">
                SIMULATOR
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">LNTFINTECH Academic Submission</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* 1-Click Role Switcher */}
          <div className="hidden lg:flex items-center bg-slate-800/80 rounded-xl p-1 border border-slate-700 text-xs">
            <span className="text-slate-400 px-2 font-medium flex items-center space-x-1">
              <UserCheck className="w-3.5 h-3.5" />
              <span>Demo Persona:</span>
            </span>
            <button
              onClick={() => handleDemoSwitch('admin@lntfintech.edu', 'Admin@12345')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                user?.role === 'ADMIN' ? 'bg-teal-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              Admin
            </button>
            <button
              onClick={() => handleDemoSwitch('merchant.acme@lntfintech.edu', 'Merchant@12345')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                user?.email === 'merchant.acme@lntfintech.edu' ? 'bg-teal-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              Acme Merchant
            </button>
            <button
              onClick={() => handleDemoSwitch('merchant.nova@lntfintech.edu', 'Merchant@12345')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                user?.email === 'merchant.nova@lntfintech.edu' ? 'bg-teal-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              Nova Merchant
            </button>
            <button
              onClick={() => handleDemoSwitch('customer1@lntfintech.edu', 'Customer@12345')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                user?.email === 'customer1@lntfintech.edu' ? 'bg-teal-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              Rahul (Customer)
            </button>
            <button
              onClick={() => handleDemoSwitch('customer2@lntfintech.edu', 'Customer@12345')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                user?.email === 'customer2@lntfintech.edu' ? 'bg-teal-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              Priya (Customer)
            </button>
          </div>

          {user ? (
            <div className="flex items-center space-x-3">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-semibold text-slate-200">{user.full_name}</div>
                <div className="text-[11px] text-teal-400 font-mono">
                  {user.role} {user.merchant_name ? `• ${user.merchant_name}` : ''}
                </div>
              </div>
              <button
                onClick={handleLogout}
                title="Sign out"
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 rounded-xl font-semibold text-xs transition-colors"
            >
              Sign In
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
