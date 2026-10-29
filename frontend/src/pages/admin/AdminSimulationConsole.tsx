import React, { useEffect, useState } from 'react';
import { Sliders, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw, XCircle } from 'lucide-react';
import { api } from '../../services/api';
import { SimulationScenario } from '../../types';

export const AdminSimulationConsole: React.FC = () => {
  const [scenarios, setScenarios] = useState<SimulationScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [bannerMsg, setBannerMsg] = useState<string | null>(null);

  const loadScenarios = async () => {
    try {
      const res = await api.getScenarios();
      setScenarios(res);
    } catch (err) {
      console.error('Failed to load scenarios:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScenarios();
  }, []);

  const handleToggle = async (scenario: SimulationScenario) => {
    setUpdating(scenario.name);
    try {
      await api.updateScenario(scenario.name, {
        is_active: !scenario.is_active,
        apply_to_next_only: !scenario.is_active,
      });
      setBannerMsg(
        !scenario.is_active
          ? `Scenario '${scenario.name}' ACTIVATED for the next transaction!`
          : `Scenario '${scenario.name}' deactivated.`
      );
      await loadScenarios();
    } catch (err) {
      console.error('Failed to update scenario:', err);
    } finally {
      setUpdating(null);
    }
  };

  const handleClearAll = async () => {
    setLoading(true);
    try {
      await api.clearAllScenarios();
      setBannerMsg('All simulation scenarios cleared. Default normal behavior restored.');
      await loadScenarios();
    } catch (err) {
      console.error('Failed to clear scenarios:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-medium text-slate-500 animate-pulse">Loading simulation engine...</div>
      </div>
    );
  }

  const activeScenario = scenarios.find((s) => s.is_active);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Simulation Console</h1>
          <p className="text-xs text-slate-500">Inject deterministic edge cases, network failures & bank discrepancies</p>
        </div>
        <button
          onClick={handleClearAll}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
        >
          <XCircle className="w-4 h-4 text-slate-500" />
          <span>Reset to Normal (Clear All)</span>
        </button>
      </div>

      {bannerMsg && (
        <div className="p-4 bg-teal-50 border border-teal-200 rounded-2xl text-xs text-teal-800 font-medium flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
            <span>{bannerMsg}</span>
          </div>
          <button onClick={() => setBannerMsg(null)} className="text-teal-600 hover:text-teal-800 text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Active banner indicator */}
      <div className="p-5 bg-slate-900 text-white rounded-2xl shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-amber-500/20 text-amber-400 rounded-xl">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-semibold uppercase">Currently Active Scenario</div>
            <div className="text-base font-bold text-white">
              {activeScenario ? (
                <span className="text-amber-400 font-mono">{activeScenario.name}</span>
              ) : (
                <span className="text-emerald-400">NORMAL OPERATION (No Faults Injected)</span>
              )}
            </div>
          </div>
        </div>
        {activeScenario && (
          <span className="text-xs bg-amber-500 text-slate-950 font-bold px-3 py-1 rounded-full animate-pulse">
            Active for Next Transaction
          </span>
        )}
      </div>

      {/* Grid of 13 Scenarios */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map((s) => (
          <div
            key={s.id}
            className={`p-5 rounded-2xl border transition-all ${
              s.is_active
                ? 'bg-amber-500/10 border-amber-500 shadow-md ring-2 ring-amber-500/30'
                : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'
            }`}
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <span className="font-mono text-xs font-bold text-slate-900 leading-tight">{s.name}</span>
              <button
                onClick={() => handleToggle(s)}
                disabled={updating === s.name}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                  s.is_active
                    ? 'bg-amber-500 text-slate-950 hover:bg-amber-600'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
              >
                {updating === s.name ? 'Saving...' : s.is_active ? 'Active' : 'Activate'}
              </button>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed min-h-[3rem]">{s.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
