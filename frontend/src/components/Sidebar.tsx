import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CreditCard,
  History,
  FileCheck2,
  Building2,
  Scale,
  Sliders,
  ShieldAlert,
  Server,
  FileText,
  DollarSign,
  Layers,
} from 'lucide-react';
import { UserRole } from '../types';

interface Props {
  role: UserRole;
}

export const Sidebar: React.FC<Props> = ({ role }) => {
  const getNavLinks = () => {
    if (role === 'CUSTOMER') {
      return [
        { to: '/customer', label: 'My Accounts & Balances', icon: <CreditCard className="w-4 h-4" /> },
        { to: '/customer/pay', label: 'Initiate Payment', icon: <DollarSign className="w-4 h-4" /> },
        { to: '/customer/transactions', label: 'My Receipts & Timeline', icon: <History className="w-4 h-4" /> },
      ];
    } else if (role === 'MERCHANT') {
      return [
        { to: '/merchant', label: 'Merchant Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
        { to: '/merchant/payments', label: 'Payments & Refunds', icon: <History className="w-4 h-4" /> },
        { to: '/merchant/settlements', label: 'Settlement Statements', icon: <FileCheck2 className="w-4 h-4" /> },
        { to: '/merchant/profile', label: 'Acquiring Profile & Fees', icon: <Building2 className="w-4 h-4" /> },
      ];
    } else {
      // ADMIN
      return [
        { to: '/admin', label: 'System Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
        { to: '/admin/scenarios', label: 'Simulation Console (13)', icon: <Sliders className="w-4 h-4 text-amber-500 font-bold" /> },
        { to: '/admin/merchants', label: 'Merchant Approvals', icon: <Building2 className="w-4 h-4" /> },
        { to: '/admin/risk', label: 'Risk Rules & Review Queue', icon: <ShieldAlert className="w-4 h-4" /> },
        { to: '/admin/settlements', label: 'Settlement Engine', icon: <Layers className="w-4 h-4" /> },
        { to: '/admin/reconciliation', label: '3-Way Reconciliation', icon: <Scale className="w-4 h-4" /> },
        { to: '/admin/routes', label: 'Bank Routes & Availability', icon: <Server className="w-4 h-4" /> },
        { to: '/admin/audit', label: 'Audit Trail & Ledger', icon: <FileText className="w-4 h-4" /> },
      ];
    }
  };

  const links = getNavLinks();

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col min-h-[calc(100vh-6rem)]">
      <div className="p-4 flex-1 space-y-1">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2">
          {role} Navigation
        </div>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/customer' || link.to === '/merchant' || link.to === '/admin'}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`
            }
          >
            {link.icon}
            <span>{link.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="text-[11px] text-slate-500 font-medium leading-relaxed">
          <strong>L&T Fintech Project</strong>
          <br />
          Switching, Acquiring, Ledger & Rec engine.
        </div>
      </div>
    </aside>
  );
};
