import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api } from './services/api';
import { User } from './types';
import { SimulationBanner } from './components/SimulationBanner';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

import { IntroPage } from './pages/public/IntroPage';
import { LoginPage } from './pages/public/LoginPage';
import { CustomerDashboard } from './pages/customer/CustomerDashboard';
import { NewPaymentPage } from './pages/customer/NewPaymentPage';
import { PaymentDetailPage } from './pages/customer/PaymentDetailPage';
import { MerchantDashboard } from './pages/merchant/MerchantDashboard';
import { MerchantSettlementsPage } from './pages/merchant/MerchantSettlementsPage';
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminSimulationConsole } from './pages/admin/AdminSimulationConsole';
import { AdminSettlementPage } from './pages/admin/AdminSettlementPage';
import { AdminReconciliationPage } from './pages/admin/AdminReconciliationPage';
import { AdminRiskPage } from './pages/admin/AdminRiskPage';
import { AdminMerchantApprovalsPage } from './pages/admin/AdminMerchantApprovalsPage';
import { AdminAuditLogsPage } from './pages/admin/AdminAuditLogsPage';

const queryClient = new QueryClient();

export const AppContent: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    async function checkAuth() {
      try {
        const u = await api.getCurrentUser();
        setUser(u);
      } catch (err) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    checkAuth();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-semibold text-slate-500">Initializing Payment Switch Simulator...</p>
        </div>
      </div>
    );
  }

  const isPublicPage = location.pathname === '/' || location.pathname === '/login';

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <SimulationBanner />
      <Navbar user={user} onUserSwitch={(newUser) => setUser(newUser)} />

      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {user && !isPublicPage && <Sidebar role={user.role} />}

        <main className={`flex-1 p-6 sm:p-8 ${!user || isPublicPage ? 'w-full' : ''}`}>
          <Routes>
            <Route path="/" element={<IntroPage />} />
            <Route path="/login" element={<LoginPage onLoginSuccess={(u) => setUser(u)} />} />

            {/* Customer Routes */}
            <Route
              path="/customer"
              element={user?.role === 'CUSTOMER' || user?.role === 'ADMIN' ? <CustomerDashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/customer/pay"
              element={user?.role === 'CUSTOMER' || user?.role === 'ADMIN' ? <NewPaymentPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/customer/transactions"
              element={user?.role === 'CUSTOMER' || user?.role === 'ADMIN' ? <CustomerDashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/customer/payments/:id"
              element={user ? <PaymentDetailPage /> : <Navigate to="/login" />}
            />

            {/* Merchant Routes */}
            <Route
              path="/merchant"
              element={user?.role === 'MERCHANT' || user?.role === 'ADMIN' ? <MerchantDashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/merchant/payments"
              element={user?.role === 'MERCHANT' || user?.role === 'ADMIN' ? <MerchantDashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/merchant/settlements"
              element={user?.role === 'MERCHANT' || user?.role === 'ADMIN' ? <MerchantSettlementsPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/merchant/profile"
              element={user?.role === 'MERCHANT' || user?.role === 'ADMIN' ? <MerchantDashboard /> : <Navigate to="/login" />}
            />

            {/* Admin Routes */}
            <Route
              path="/admin"
              element={user?.role === 'ADMIN' ? <AdminDashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/admin/scenarios"
              element={user?.role === 'ADMIN' ? <AdminSimulationConsole /> : <Navigate to="/login" />}
            />
            <Route
              path="/admin/settlements"
              element={user?.role === 'ADMIN' ? <AdminSettlementPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/admin/reconciliation"
              element={user?.role === 'ADMIN' ? <AdminReconciliationPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/admin/risk"
              element={user?.role === 'ADMIN' ? <AdminRiskPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/admin/merchants"
              element={user?.role === 'ADMIN' ? <AdminMerchantApprovalsPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/admin/audit"
              element={user?.role === 'ADMIN' ? <AdminAuditLogsPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/admin/routes"
              element={user?.role === 'ADMIN' ? <AdminSimulationConsole /> : <Navigate to="/login" />}
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
