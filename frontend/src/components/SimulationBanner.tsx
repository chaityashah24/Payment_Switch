import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export const SimulationBanner: React.FC = () => {
  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-xs text-amber-900 flex items-center justify-between">
      <div className="flex items-center space-x-2 max-w-7xl mx-auto w-full">
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <span className="font-semibold text-amber-800 tracking-wide uppercase">
          Academic Simulation Environment:
        </span>
        <span className="text-amber-800/90 truncate">
          This system is an educational payment switch and merchant acquiring simulator for LNTFINTECH. No real banks, NPCI, or real card networks are connected. All currency (INR) and instruments are fictional.
        </span>
      </div>
      <div className="hidden md:flex items-center space-x-1.5 text-amber-800 text-[11px] font-medium pl-4">
        <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
        <span>Double-Entry Ledger Active</span>
      </div>
    </div>
  );
};
