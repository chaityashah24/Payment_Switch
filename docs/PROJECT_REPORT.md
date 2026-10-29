# LNTFINTECH Academic Project Submission
# Secure Payment Switch & Merchant Acquiring Simulator
**Project Report**

---

## 1. Abstract
The **Secure Payment Switch & Merchant Acquiring Simulator** is a full-stack educational and experimental software platform developed for LNTFINTECH academic submission. It simulates the end-to-end lifecycle of retail electronic payments across four foundational payment rails: **Unified Payments Interface (UPI)**, **Tokenized Payment Cards**, **National Electronic Funds Transfer (NEFT)**, and **Real-Time Gross Settlement (RTGS)**. 

The platform demonstrates how customer transactions are accepted for registered merchants, evaluated against anti-fraud risk rules, routed through an intelligent payment switch, processed by simulated issuing/clearing bank cores, posted to an immutable double-entry accounting ledger with integer-paise precision, settled in merchant batches with snapshot fee structures, and audited through automated three-way reconciliation. In addition, an administrative simulation console injects 13 deterministic network and operational anomalies (including downtime, timeouts with unknown outcomes, amount/status discrepancies, and payout failures) to demonstrate fault-tolerance and distributed financial invariants.

> [!IMPORTANT]
> **Academic Simulation Disclaimer:** This software is an educational simulation. It does NOT connect to production banking hosts, the National Payments Corporation of India (NPCI), the Reserve Bank of India (RBI), or real card networks (Visa/Mastercard/RuPay). It collects no live PANs, CVVs, net banking credentials, or production biometric/OTP tokens.

---

## 2. Problem Statement & Motivation
Modern digital financial infrastructure is inherently distributed, asynchronous, and mission-critical. Traditional academic coursework frequently focuses on basic database CRUD operations or e-commerce carts without exposing students to the core engineering challenges of financial switching:
1. **Network Non-Determinism & Timeouts:** In distributed systems, a network timeout does not imply failure. If a gateway times out after the issuing bank has debited funds, naive retries cause duplicate customer debits, while naive failures cause customer fund leakage.
2. **Double-Entry Financial Invariants:** Floating-point rounding errors and single-entry balance mutations corrupt financial state. A robust platform requires atomic, double-entry journal entries where debits strictly balance credits.
3. **Idempotency Under Concurrency:** High-concurrency payment initiation requires cryptographically verifiable canonical request hashing and database-enforced deduplication.
4. **Three-Way Reconciliation:** Ensuring that switch transactions, independent external bank records, and internal accounting ledger balances remain congruent is essential for mitigating operational risk.

This project was conceived to solve these educational gaps by providing a runnable, fully audited reference architecture.

---

## 3. Project Objectives
- **Multi-Method Transaction Simulation:** Implement distinct behavioral models for UPI, tokenized Cards (auth vs. capture), NEFT (batch clearing), and RTGS (gross settlement with thresholds).
- **Merchant Acquiring & Fee Snapshots:** Support onboarding, role-based merchant management, and deterministic snapshot fee deductions (basis points and fixed paise).
- **Resilient State Management:** Model explicit payment state machines with zero tolerance for illegal transitions (e.g., successful payments transitioning to failed).
- **Double-Entry General Ledger:** Enforce `Σ(Debits) == Σ(Credits)` using integer paise arithmetic and balance holds.
- **Idempotency Engine:** Provide canonical payload fingerprinting preventing duplicate charges under concurrent initiation.
- **Settlement & Retry:** Calculate gross sales, fee deductions, and refund adjustments per cutoff, with safe payout retry semantics.
- **Three-Way Reconciliation Engine:** Independently compare switch logs, bank core transactions, and ledger entries to detect missing records, status mismatches, and amount discrepancies.
- **Scenario Injection Console:** Support 13 named simulation scenarios to test edge cases deterministically.

---

## 4. System Boundaries & Scope
- **In Scope:**
  - Customer self-service portal (account balances, test instruments, payment initiation, receipts).
  - Merchant portal (payments list, order search, partial/full refunds, settlement statements).
  - Administrator portal (simulation console, route management, risk rules, review queue, settlement batch execution, reconciliation exception resolution, audit logs).
  - Background asynchronous worker for delayed payments, NEFT batch processing, and payout retries.
  - Complete RESTful API v1 with OpenAPI documentation.
- **Out of Scope (By Design):**
  - Live bank network interfaces or real ISO 8583 / ISO 20022 clearing networks.
  - Collection or storage of real payment instruments, PCI DSS hardware security modules (HSM), or live KYC data.
  - Multi-currency forex arbitrage (system operates in integer paise INR).

---

## 5. Technology Architecture
The platform is built as a **Modular Monolith** to maximize conceptual clarity, local testability, and deterministic reproducibility:
- **Backend Framework:** Python 3.9+ with **FastAPI** for high-performance asynchronous API handling and schema validation.
- **Data Persistence:** **SQLAlchemy 2.0** ORM paired with PostgreSQL (and transparent SQLite fallback for zero-dependency local runs).
- **Database Migrations:** **Alembic** for version-controlled, reproducible schema evolution.
- **Background Worker:** Custom database-backed worker process utilizing atomic job claiming (`with_for_update(skip_locked=True)`) and exponential backoff.
- **Frontend Stack:** **React 18** with **TypeScript**, **Vite**, **Tailwind CSS**, and **Lucide React** icons.
- **State & Routing:** **TanStack React Query** for server state caching and **React Router v6**.
- **Data Visualization:** **Recharts** for live volume and outcome distribution charts.
- **Containerization:** **Docker Compose** orchestrating frontend, backend, background worker, and PostgreSQL containers.

---

## 6. Functional & Non-Functional Requirements

### Functional Requirements
| Module | Requirement Description |
| :--- | :--- |
| **Auth & RBAC** | Bcrypt password hashing, HttpOnly JWT cookies, strict role segregation (`CUSTOMER`, `MERCHANT`, `ADMIN`). |
| **Switch Routing** | Dynamic route selection by payment method and bank priority; bank availability toggles. |
| **Ledger Engine** | Integer paise storage, multi-account double-entry journals, balance holds, and atomic consistency verification. |
| **Merchant Acquiring**| Snapshot fees (`fee_percentage_bps` and `fee_flat_paise`), statuses (`PENDING`, `APPROVED`, `SUSPENDED`). |
| **Refund Engine** | Idempotent partial and full refunds; over-refund prevention; proportional fee reversal; ledger reversal. |
| **Settlement** | Configurable cutoff timestamps; batch preview; merchant payout generation; idempotent payout retry. |
| **Reconciliation** | Three-way comparison (Switch vs. Bank Core vs. Ledger); exception severity categorization; recorded resolution. |
| **Risk Engine** | Configurable velocity, amount, and repeated-merchant rules; automated `ALLOW`, `DECLINE`, or `REVIEW`. |

### Non-Functional Requirements
- **Financial Invariance:** Zero floating-point arithmetic; strict equality of debits and credits.
- **Deterrent Security:** Redaction of sensitive fields in application logs; correlation IDs across all requests.
- **Determinism:** Scenarios execute predictably without uncontrolled random flakiness.
- **Observability:** Complete audit logs tracking actor, action, timestamp, and entity diff.

---

## 7. Verification & Test Summary
The platform includes an extensive automated test suite covering:
1. **Double-Entry Ledger Invariance:** Verified `Σ(Debits) == Σ(Credits)` and guaranteed rejection of imbalanced entries.
2. **Idempotency Under Concurrency:** Validated that identical requests return cached payment outcomes, while identical keys with altered payloads return HTTP 409 Conflict.
3. **Multi-Method Behavior:** Verified UPI MPIN validation, Card authorization hold vs. capture, NEFT queue state, and RTGS threshold enforcement.
4. **Resilience & Timeouts:** Verified that `TIMEOUT_AFTER_BANK_SUCCESS` leaves the transaction in `PENDING` with active balance hold until resolved, preventing double-debits.
5. **Refund Limits:** Verified rejection of refund amounts exceeding the captured payment value.
6. **Settlement Deduplication:** Verified that payments allocated to a settlement batch cannot be selected in subsequent batches.

**Test Execution Results:** 19 out of 19 automated Pytest test modules passed with 100% green status.

---

## 8. Limitations & Future Scope
- **Current Limitations:**
  - Webhooks are modeled via internal simulator events rather than internet-facing endpoints.
  - Multi-currency exchange rate adjustments are not modeled (locked to INR).
- **Future Scope:**
  - Implementation of simulated ISO 20022 XML messaging payloads for RTGS.
  - Integration of client-side biometric WebAuthn challenges for customer authentication.
  - Distributed event streaming via Apache Kafka for multi-node switch scaling demonstrations.
