# Secure Payment Switch & Merchant Acquiring Simulator
## Payment Lifecycle, State Machines & Transaction Sequences

---

## 1. Payment State Machine Specification

Transactions within the payment switch adhere to a deterministic finite state machine (FSM). Illegal state transitions (e.g., attempting to transition a `CAPTURED` payment to `FAILED`, or transitioning from `REVERSED` to `AUTHORIZED`) are strictly rejected by the core state machine (`app/core/state_machine.py`) with a domain exception.

```mermaid
stateDiagram-v2
    [*] --> CREATED : Client initiates payment
    CREATED --> PENDING : Under Risk Review / Batch Queued / Network Timeout
    CREATED --> AUTHORIZED : Two-Phase Card Auth Succeeded
    CREATED --> CAPTURED : Immediate Debit Succeeded (UPI / RTGS / Instant Card)
    CREATED --> FAILED : Validation / Risk / Auth Decline

    PENDING --> CAPTURED : Batch Cleared / Poller Confirms Bank Success
    PENDING --> FAILED : Poller Confirms Bank Decline / Timeout Expired

    AUTHORIZED --> CAPTURED : Merchant Captures Auth Hold
    AUTHORIZED --> REVERSED : Merchant Cancels Auth / Hold Expires

    CAPTURED --> PARTIALLY_REFUNDED : Eligible Partial Refund Executed
    CAPTURED --> REFUNDED : Full Refund Executed

    PARTIALLY_REFUNDED --> PARTIALLY_REFUNDED : Additional Partial Refund Executed
    PARTIALLY_REFUNDED --> REFUNDED : Cumulative Refunds Equal 100% Amount

    FAILED --> [*]
    REVERSED --> [*]
    REFUNDED --> [*]
```

### Transition Validity Matrix
| Current State | Target State | Permitted? | Trigger / Context |
|---|---|---|---|
| `CREATED` | `PENDING` | Yes | NEFT batch queue, high risk review, bank network timeout |
| `CREATED` | `AUTHORIZED` | Yes | Card authorization hold successful |
| `CREATED` | `CAPTURED` | Yes | Instant one-phase capture (UPI, RTGS, Instant Card) |
| `CREATED` | `FAILED` | Yes | Insufficient funds, bad MPIN/token, bank downtime |
| `PENDING` | `CAPTURED` | Yes | Async worker NEFT batch cleared, status poller confirmation |
| `PENDING` | `FAILED` | Yes | Async worker confirms bank decline or hard timeout |
| `AUTHORIZED`| `CAPTURED` | Yes | Merchant or switch executes capture against active balance hold |
| `AUTHORIZED`| `REVERSED` | Yes | Card authorization expired or voided before capture |
| `CAPTURED` | `REFUNDED` | Yes | Full refund successfully posted |
| `CAPTURED` | `PARTIALLY_REFUNDED`| Yes | Partial refund posted |
| `CAPTURED` | `FAILED` | **No** | **Illegal Transition:** Funds were already debited and posted |
| `FAILED` | `CAPTURED` | **No** | **Illegal Transition:** Failed payments cannot be resurrected |

---

## 2. Payment Rail Transaction Sequences

### 2.1 UPI Payment Sequence (Instant Debit & Capture)
Unified Payments Interface (UPI) provides instant account-to-account credit transfer using Virtual Payment Addresses (VPAs) and a mobile PIN (MPIN).

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant Switch as Payment Switch Core
    participant Adapter as UPI Bank Adapter
    participant BankHost as Simulated Bank Host
    participant Ledger as General Ledger

    Customer->>UI: Selects UPI, enters VPA (e.g. rahul@okhdfc) & MPIN
    UI->>API: POST /api/v1/payments (Idempotency-Key, Amount, VPA, MPIN)
    API->>Switch: initiate_payment(payload)
    Switch->>Switch: Validate VPA regex & Idempotency Key
    Switch->>Adapter: process_payment(customer_acc, vpa, mpin, amount)
    Adapter->>BankHost: Validate MPIN credential
    alt Invalid MPIN
        BankHost-->>Adapter: AUTH_FAILED
        Adapter-->>Switch: Result(FAILED, "Invalid UPI MPIN")
        Switch->>API: 400 Bad Request / FAILED
        API-->>Customer: "Payment Failed: Invalid MPIN"
    else Valid MPIN & Sufficient Funds
        BankHost->>BankHost: Atomic Debit Customer & Credit Pool
        BankHost-->>Adapter: SUCCESS (BankRef: UPI-849204)
        Adapter-->>Switch: Result(CAPTURED, BankRef)
        Switch->>Ledger: Post Double-Entry Journal (Debit Cash, Credit Merchant Payable, Credit Fee)
        Switch-->>API: 200 OK (Payment CAPTURED)
        API-->>UI: Display Success & Downloadable Receipt
    end
```

---

### 2.2 Card Payment Sequence (Two-Phase Authorization & Capture)
Card payments decouple fund reservation (authorization hold) from final merchant settlement capture.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant Switch as Payment Switch Core
    participant CardAdapter as Card Bank Adapter
    participant BankHost as Simulated Bank Host
    participant Ledger as General Ledger

    Customer->>UI: Selects Saved Card Token
    UI->>API: POST /api/v1/payments (Method: CARD, Token, AutoCapture: False)
    API->>Switch: initiate_payment()
    Switch->>CardAdapter: authorize(card_token, amount)
    CardAdapter->>BankHost: Place BalanceHold on Customer Account
    BankHost-->>CardAdapter: Hold Created (HoldId: HLD-102)
    CardAdapter-->>Switch: Result(AUTHORIZED, HoldId)
    Switch-->>API: 200 OK (Status: AUTHORIZED)
    Note over Customer,Switch: Funds are held/reserved. Not yet recognized as merchant revenue.

    Note over Switch,Ledger: Phase 2: Capture Event (Immediate or Delayed)
    API->>Switch: capture_payment(payment_id)
    Switch->>CardAdapter: capture(HoldId)
    CardAdapter->>BankHost: Release Hold & Debit Balance
    BankHost-->>CardAdapter: Debited & Confirmed
    CardAdapter-->>Switch: Result(CAPTURED)
    Switch->>Ledger: Post Revenue & Merchant Payable Journal Lines
    Switch-->>API: 200 OK (Status: CAPTURED)
```

---

### 2.3 NEFT Simulation Sequence (Batch Queuing)
NEFT simulates Indian deferred net settlement batches. Payments are accepted into a queue and cleared periodically by the background worker.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant API as FastAPI Gateway
    participant Switch as Payment Switch Core
    participant DB as Relational Database
    participant Worker as Background Job Worker
    participant BankHost as Simulated Bank Host
    participant Ledger as General Ledger

    Customer->>API: POST /api/v1/payments (Method: NEFT, Beneficiary IFSC)
    API->>Switch: initiate_payment()
    Switch->>DB: Record Payment (Status: PENDING)
    Switch->>DB: Enqueue BackgroundJob (PROCESS_NEFT_BATCH)
    Switch-->>API: 200 OK (Status: PENDING, Message: "Queued for NEFT batch")
    API-->>Customer: "Payment Queued in NEFT Cycle"

    Note over Worker,DB: Worker executes NEFT Batch Job
    Worker->>DB: Claim pending NEFT payments
    loop For each NEFT Payment in Batch
        Worker->>BankHost: Execute inter-bank transfer
        BankHost-->>Worker: Transfer Success
        Worker->>DB: Update Payment Status -> CAPTURED
        Worker->>Ledger: Post Journal Entry
    end
    Worker->>DB: Mark Job COMPLETED
```

---

### 2.4 RTGS Simulation Sequence (Real-Time Gross Settlement)
RTGS handles large-value transactions with strict eligibility rules (minimum ₹2,00,000 / 20,000,000 paise).

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant API as FastAPI Gateway
    participant Switch as Payment Switch Core
    participant RTGSAdapter as RTGS Bank Adapter
    participant BankHost as Simulated Bank Host

    Customer->>API: POST /api/v1/payments (Method: RTGS, Amount: ₹1,50,000)
    API->>Switch: initiate_payment()
    Switch->>RTGSAdapter: validate_and_route()
    alt Amount < ₹2,00,000
        RTGSAdapter-->>Switch: REJECTED ("RTGS minimum threshold is ₹2,00,000")
        Switch-->>API: 422 Unprocessable Entity
        API-->>Customer: Error: "RTGS threshold not met. Use NEFT or UPI."
    else Amount >= ₹2,00,000
        RTGSAdapter->>BankHost: Direct gross nodal debit & credit
        BankHost-->>RTGSAdapter: Immediate Clearing Success
        RTGSAdapter-->>Switch: Result(CAPTURED)
        Switch-->>API: 200 OK (Status: CAPTURED)
    end
```

---

### 2.5 Timeout-After-Bank-Success Sequence (Distributed Ambiguity)
Demonstrates the most critical payment failure mode: the bank successfully debits the customer, but the response network connection drops before reaching the switch.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant Switch as Payment Switch Core
    participant BankAdapter as Bank Adapter
    participant BankHost as Simulated Bank Host
    participant Worker as Background Worker
    participant Ledger as General Ledger

    Customer->>Switch: Initiate Payment (₹5,000)
    Switch->>BankAdapter: Debit Customer Account
    BankAdapter->>BankHost: Account Debited Successfully (Bank Txn Recorded)
    Note over BankAdapter,Switch: SIMULATION INJECTION: Network Timeout Dropped!
    BankAdapter--xSwitch: HTTP Connection Timeout / Drop
    
    Note over Switch: Switch does NOT mark FAILED (would cause customer fund loss).
    Switch->>Switch: Transition Status -> PENDING (Ambiguous Outcome)
    Switch->>Worker: Enqueue POLL_TIMEOUT_PAYMENTS Job
    Switch-->>Customer: 202 Accepted ("Processing: Bank verification in progress")

    Note over Worker,BankHost: Asynchronous Resolution Loop
    Worker->>BankHost: Query Bank Transaction Status (TxnRef / IdempotencyKey)
    BankHost-->>Worker: Status: CONFIRMED_DEBITED (TxnRef: BNK-9921)
    Worker->>Switch: Mark Payment CAPTURED
    Worker->>Ledger: Post Double-Entry Journal Entry
    Note over Customer,Worker: Payment safely resolved without double-debiting or fund loss!
```

---

### 2.6 Refund Execution Sequence
Demonstrates partial or full refund with ledger reversals.

```mermaid
sequenceDiagram
    autonumber
    actor Merchant as Merchant
    participant API as FastAPI Gateway
    participant RefundSvc as Refund Service
    participant BankHost as Simulated Bank Host
    participant Ledger as General Ledger

    Merchant->>API: POST /api/v1/refunds (PaymentId, AmountPaise, Reason)
    API->>RefundSvc: process_refund()
    RefundSvc->>RefundSvc: Verify Payment is CAPTURED
    RefundSvc->>RefundSvc: Verify (Existing Refunds + New Refund) <= Original Amount
    RefundSvc->>BankHost: Credit Customer Account & Debit Merchant Account
    BankHost-->>RefundSvc: Funds Reversal Confirmed
    RefundSvc->>Ledger: Post Refund Journal Entry (Debit Merchant Payable, Credit Customer Cash)
    RefundSvc->>RefundSvc: Update Payment Status (PARTIALLY_REFUNDED or REFUNDED)
    RefundSvc-->>API: 200 OK (Refund Record)
    API-->>Merchant: Refund Successfully Processed
```

---

### 2.7 Settlement Batch & Payout Sequence
Aggregates eligible transactions, deducts snapshot fees, and transfers net funds to the merchant's simulated nodal account.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin / Cron
    participant SettleSvc as Settlement Service
    participant DB as Relational Database
    participant BankHost as Simulated Bank Host
    participant Ledger as General Ledger

    Admin->>SettleSvc: trigger_settlement_batch(merchant_id, cutoff_time)
    SettleSvc->>DB: Query CAPTURED & UNSETTLED payments
    SettleSvc->>SettleSvc: Compute Gross (₹1,00,000), Fees (₹1,750), Refunds (₹5,000)
    SettleSvc->>SettleSvc: Compute Net Payout: ₹93,250
    SettleSvc->>DB: Insert SettlementBatch (Status: CALCULATED) & Link Items
    
    SettleSvc->>BankHost: Transfer Net Payout to Merchant Settlement Account
    alt Payout Succeeded
        BankHost-->>SettleSvc: Payout Confirmed
        SettleSvc->>DB: Mark Batch SETTLED, Payments SETTLED
        SettleSvc->>Ledger: Post Settlement Journal (Debit Merchant Payable, Credit Nodal Reserve)
    else Nodal Payout Failed (Simulated Scenario)
        BankHost-->>SettleSvc: PAYOUT_DECLINED
        SettleSvc->>DB: Mark Batch FAILED
        SettleSvc->>DB: Enqueue Retry Job for Admin Intervention
    end
```

---

### 2.8 Three-Way Reconciliation Sequence
Demonstrates automated cross-comparison between switch logs, bank statements, and ledger balances.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin / Audit
    participant ReconSvc as Reconciliation Service
    participant SwitchDB as Switch Payments Table
    participant BankHost as Bank Transactions Table
    participant LedgerDB as Journal Lines Table

    Admin->>ReconSvc: run_reconciliation(date_range)
    ReconSvc->>SwitchDB: Fetch all captured payments
    ReconSvc->>BankHost: Fetch all debited external transactions
    ReconSvc->>LedgerDB: Fetch all journal lines

    loop For every transaction record
        ReconSvc->>ReconSvc: Match on External Ref & Idempotency Key
        alt All three records match in status and amount
            ReconSvc->>ReconSvc: Mark MATCHED
        else Bank record exists but missing in Switch
            ReconSvc->>DB: Insert ReconciliationException(MISSING_IN_SWITCH)
        else Switch is CAPTURED but Bank is FAILED
            ReconSvc->>DB: Insert ReconciliationException(STATUS_MISMATCH)
        else Switch amount != Bank debited amount
            ReconSvc->>DB: Insert ReconciliationException(AMOUNT_MISMATCH)
        end
    end
    ReconSvc-->>Admin: Reconciliation Summary (Total, Matched, Exceptions)
```
