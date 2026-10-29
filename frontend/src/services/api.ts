const BASE_URL = '/api/v1';

export class ApiError extends Error {
  code: string;
  status: number;
  correlation_id?: string;
  details?: any;

  constructor(code: string, message: string, status: number, correlation_id?: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.correlation_id = correlation_id;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('switch_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorInfo = data.error || {};
    throw new ApiError(
      errorInfo.code || 'REQUEST_FAILED',
      errorInfo.message || `Request failed with status ${response.status}`,
      response.status,
      errorInfo.correlation_id,
      errorInfo.details
    );
  }

  return data as T;
}

export const api = {
  // Auth
  login: (data: any) => request<any>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request<any>('/auth/logout', { method: 'POST' }),
  getCurrentUser: () => request<any>('/auth/me'),
  registerCustomer: (data: any) => request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  // Accounts & Instruments
  getAccounts: () => request<any[]>('/accounts'),
  getInstruments: () => request<any[]>('/accounts/instruments'),
  registerInstrument: (data: any) => request<any>('/accounts/instruments', { method: 'POST', body: JSON.stringify(data) }),
  getBanks: () => request<any[]>('/accounts/banks'),

  // Merchants
  getMerchants: (statusFilter?: string) => request<any[]>(`/merchants${statusFilter ? `?status_filter=${statusFilter}` : ''}`),
  getMerchantProfile: () => request<any>('/merchants/me'),
  onboardMerchant: (data: any) => request<any>('/merchants/onboard', { method: 'POST', body: JSON.stringify(data) }),
  reviewMerchant: (id: string, data: any) => request<any>(`/merchants/${id}/review`, { method: 'POST', body: JSON.stringify(data) }),

  // Payments
  initiatePayment: (data: any) => request<any>('/payments', { method: 'POST', body: JSON.stringify(data) }),
  getPayments: (params: string = '') => request<any[]>(`/payments${params ? `?${params}` : ''}`),
  getPaymentDetails: (id: string) => request<any>(`/payments/${id}`),
  getPaymentTimeline: (id: string) => request<any[]>(`/payments/${id}/timeline`),
  getPaymentReceipt: (id: string) => request<any>(`/payments/${id}/receipt`),
  resolvePaymentStatus: (id: string) => request<any>(`/payments/${id}/resolve`, { method: 'POST' }),

  // Refunds
  createRefund: (data: any) => request<any>('/refunds', { method: 'POST', body: JSON.stringify(data) }),
  getRefunds: (params: string = '') => request<any[]>(`/refunds${params ? `?${params}` : ''}`),

  // Settlements
  getSettlementPreview: () => request<any>('/settlements/preview'),
  createSettlementBatch: (data: any = {}) => request<any>('/settlements/batch', { method: 'POST', body: JSON.stringify(data) }),
  getSettlementBatches: () => request<any[]>('/settlements/batches'),
  getSettlementBatchDetails: (id: string) => request<any>(`/settlements/batches/${id}`),
  retrySettlementPayout: (itemId: string) => request<any>(`/settlements/items/${itemId}/retry`, { method: 'POST' }),
  getMerchantSettlements: () => request<any[]>('/settlements/merchant'),

  // Reconciliation
  triggerReconciliation: (data: any) => request<any>('/reconciliation/run', { method: 'POST', body: JSON.stringify(data) }),
  getReconciliationRuns: () => request<any[]>('/reconciliation/runs'),
  getReconciliationRunDetails: (id: string) => request<any>(`/reconciliation/runs/${id}`),
  getReconciliationExceptions: () => request<any[]>('/reconciliation/exceptions'),
  resolveException: (id: string, data: any) => request<any>(`/reconciliation/exceptions/${id}/resolve`, { method: 'POST', body: JSON.stringify(data) }),

  // Risk
  getRiskRules: () => request<any[]>('/risk/rules'),
  createRiskRule: (data: any) => request<any>('/risk/rules', { method: 'POST', body: JSON.stringify(data) }),
  getReviewQueue: () => request<any[]>('/risk/review-queue'),
  resolveRiskReview: (paymentId: string, data: any) => request<any>(`/risk/review-queue/${paymentId}/resolve`, { method: 'POST', body: JSON.stringify(data) }),

  // Scenarios
  getScenarios: () => request<any[]>('/scenarios'),
  updateScenario: (name: string, data: any) => request<any>(`/scenarios/${name}`, { method: 'PUT', body: JSON.stringify(data) }),
  clearAllScenarios: () => request<any>('/scenarios/clear-all', { method: 'POST' }),

  // Admin System Management
  getRoutes: () => request<any[]>('/admin/routes'),
  toggleRoute: (id: string) => request<any>(`/admin/routes/${id}/toggle`, { method: 'PUT' }),
  getBanksAdmin: () => request<any[]>('/admin/banks'),
  toggleBank: (id: string) => request<any>(`/admin/banks/${id}/toggle`, { method: 'PUT' }),
  getBackgroundJobs: () => request<any[]>('/admin/jobs'),
  getLedgerIntegrity: () => request<any>('/admin/ledger/integrity'),
  getAuditLogs: () => request<any[]>('/admin/audit-logs'),

  // Reports
  getDashboardMetrics: () => request<any>('/reports/dashboard'),
};
