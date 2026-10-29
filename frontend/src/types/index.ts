export type UserRole = 'CUSTOMER' | 'MERCHANT' | 'ADMIN';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  merchant_id?: string;
  merchant_name?: string;
  created_at: string;
}

export interface Bank {
  id: string;
  code: string;
  name: string;
  ifsc_prefix: string;
  is_available: boolean;
  latency_ms: number;
  downtime_until?: string;
}

export interface SimulatedAccount {
  id: string;
  account_number: string;
  account_type: string;
  balance_paise: number;
  available_balance_paise: number;
  currency: string;
  bank: Bank;
}

export interface PaymentInstrument {
  id: string;
  instrument_type: 'UPI_VPA' | 'CARD_TOKEN' | 'BANK_ACCOUNT';
  masked_identifier: string;
  token_ref: string;
  card_brand?: string;
  expiry_month?: number;
  expiry_year?: number;
  is_active: boolean;
  created_at: string;
}

export type PaymentMethod = 'UPI' | 'CARD' | 'NEFT' | 'RTGS';

export type PaymentStatus =
  | 'CREATED'
  | 'AUTHENTICATION_REQUIRED'
  | 'QUEUED'
  | 'PROCESSING'
  | 'PENDING'
  | 'SUCCEEDED'
  | 'DECLINED'
  | 'FAILED'
  | 'CANCELLED';

export interface PaymentEvent {
  id: string;
  event_type: string;
  from_status?: string;
  to_status: string;
  correlation_id?: string;
  details?: string;
  created_at: string;
}

export interface Payment {
  id: string;
  customer_id: string;
  merchant_id: string;
  merchant_name?: string;
  payment_method: PaymentMethod;
  amount_paise: number;
  currency: string;
  status: PaymentStatus;
  fee_bps_snapshot: number;
  fee_flat_paise_snapshot: number;
  calculated_fee_paise: number;
  net_merchant_paise: number;
  merchant_order_ref?: string;
  idempotency_key?: string;
  instrument_ref?: string;
  bank_reference?: string;
  active_scenario?: string;
  error_code?: string;
  error_message?: string;
  settled_item_id?: string;
  total_refunded_paise: number;
  created_at: string;
  updated_at: string;
  events?: PaymentEvent[];
}

export interface Merchant {
  id: string;
  business_name: string;
  contact_email: string;
  business_category: string;
  settlement_account_ref: string;
  supported_methods: string;
  fee_percentage_bps: number;
  fee_flat_paise: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'SUSPENDED';
  rejection_reason?: string;
  created_at: string;
  approved_at?: string;
}

export interface Refund {
  id: string;
  payment_id: string;
  merchant_id: string;
  amount_paise: number;
  fee_refund_paise: number;
  currency: string;
  reason: string;
  idempotency_key: string;
  status: 'PENDING' | 'SUCCEEDED' | 'FAILED';
  bank_reference?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface SettlementItem {
  id: string;
  settlement_batch_id: string;
  merchant_id: string;
  merchant_name?: string;
  gross_amount_paise: number;
  fee_amount_paise: number;
  refund_amount_paise: number;
  net_payable_paise: number;
  payout_reference?: string;
  status: 'PENDING' | 'PAID' | 'FAILED';
  retry_count: number;
  last_error?: string;
  created_at: string;
  updated_at: string;
}

export interface SettlementBatch {
  id: string;
  batch_reference: string;
  cutoff_timestamp: string;
  status: 'CREATED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'PARTIALLY_FAILED';
  total_gross_paise: number;
  total_fee_paise: number;
  total_refund_adjustment_paise: number;
  total_net_paise: number;
  created_at: string;
  completed_at?: string;
  items?: SettlementItem[];
}

export interface ReconciliationException {
  id: string;
  reconciliation_run_id: string;
  exception_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED';
  payment_id?: string;
  bank_transaction_id?: string;
  reference_key?: string;
  explanation: string;
  resolution_notes?: string;
  resolved_by_user_id?: string;
  created_at: string;
  resolved_at?: string;
}

export interface ReconciliationRun {
  id: string;
  run_reference: string;
  bank_id?: string;
  period_start: string;
  period_end: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  total_switch_records: number;
  total_bank_records: number;
  total_matched: number;
  total_exceptions: number;
  created_at: string;
  completed_at?: string;
  exceptions?: ReconciliationException[];
}

export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  apply_to_next_only: boolean;
  route_id?: string;
  parameters?: string;
  created_at: string;
  updated_at: string;
}

export interface RiskRule {
  id: string;
  name: string;
  description: string;
  rule_type: string;
  threshold_value: number;
  window_seconds: number;
  action: 'ALLOW' | 'DECLINE' | 'REVIEW';
  is_active: boolean;
  created_at: string;
}

export interface RiskDecision {
  id: string;
  payment_id: string;
  risk_rule_id?: string;
  action: 'ALLOW' | 'DECLINE' | 'REVIEW';
  reason: string;
  resolution_action?: string;
  resolution_notes?: string;
  created_at: string;
  resolved_at?: string;
}

export interface DashboardMetrics {
  total_transactions: number;
  succeeded_count: number;
  success_rate_percent: number;
  total_volume_paise: number;
  total_volume_inr: string;
  total_fee_paise: number;
  total_fee_inr: string;
  net_payable_paise: number;
  net_payable_inr: string;
  method_distribution: { method: string; count: number }[];
  status_distribution: { status: string; count: number }[];
}

export interface AuditLog {
  id: string;
  user_id?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  correlation_id?: string;
  ip_address?: string;
  changes?: string;
  created_at: string;
}
