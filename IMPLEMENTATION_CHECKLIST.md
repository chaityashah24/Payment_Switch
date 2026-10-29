# Secure Payment Switch & Merchant Acquiring Simulator
## Implementation Checklist & Progress Tracker

- [ ] **Phase 1: Project Skeleton, Environment & Foundation**
  - [x] Workspace inspection & dependency planning
  - [x] Python virtual environment creation
  - [ ] Backend dependency installation
  - [ ] Docker Compose & container configurations (`docker-compose.yml`, Dockerfiles)
  - [ ] Core configuration, DB engine (PostgreSQL + SQLite fallback), and Alembic
  - [ ] Base models: User, Session/Token, Merchant, Membership, Audit Log
  - [ ] Authentication (bcrypt, JWT / HttpOnly cookie session, CSRF, rate limit)
  - [ ] Role-Based Access Control (CUSTOMER, MERCHANT, ADMIN)
  - [ ] Frontend setup (Vite + React + TypeScript + Tailwind CSS + Lucide + React Router + TanStack Query)

- [ ] **Phase 2: Merchant Acquiring, Accounts & First Payment Slice**
  - [ ] Merchant onboarding schemas, models, and service (fees in bps/paise, statuses: PENDING, APPROVED, REJECTED, SUSPENDED)
  - [ ] Simulated bank accounts & customer instruments (VPA, Cards, Bank accounts)
  - [ ] Double-entry ledger foundation (integer paise, ledger accounts, journal entries & lines, balancing invariant)
  - [ ] Bank adapter interface (`BankAdapter`)
  - [ ] Simulated UPI flow (vertical slice: initiation, routing, state transition, ledger posting)
  - [ ] Transaction list, detail, and timeline APIs

- [ ] **Phase 3: Idempotency, Concurrency, State Machine & Failure Scenarios**
  - [ ] Robust idempotency framework (canonical payload fingerprinting, unique constraints)
  - [ ] State machines (Payments, Attempts, Refunds, Settlements, Reconciliation)
  - [ ] Balance holds & two-phase commits for funds
  - [ ] Database-backed worker process (safe claiming, exponential backoff, leased execution)
  - [ ] 13 Admin Simulation Scenarios (SUCCESS, INSUFFICIENT_FUNDS, TIMEOUT_AFTER_BANK_SUCCESS, etc.)
  - [ ] Independent bank records persistence & pending resolution

- [ ] **Phase 4: Multi-Method Switch, Risk Engine & Refunds**
  - [ ] Card simulation (Tokenized, Authorization hold vs Immediate/Manual capture)
  - [ ] NEFT simulation (Beneficiary, batch queuing, asynchronous batch settlement)
  - [ ] RTGS simulation (High-value rule threshold, immediate gross settlement)
  - [ ] Configurable Risk Rules Engine (amount threshold, velocity windows, review queue)
  - [ ] Refunds Service (full/partial, idempotency, ledger reversals, post-settlement negative carry forward)

- [ ] **Phase 5: Settlement, 3-Way Reconciliation & Dashboards**
  - [ ] Settlement engine (preview, cutoff date, batch generation, gross, fees, net payable, payout retry)
  - [ ] 3-Way Reconciliation engine (Switch vs Independent Bank Records vs Ledger Postings)
  - [ ] Reconciliation exception tracking & resolution workflow
  - [ ] Comprehensive UI dashboards (Customer Portal, Merchant Portal, Admin Console)
  - [ ] Rich Payment Detail view with timeline, audit trail, risk result, and accounting ledger inspector

- [ ] **Phase 6: Testing, Documentation & Submission Deliverables**
  - [ ] Seed data CLI (`python -m app.cli seed`) & Safe demo reset CLI (`python -m app.cli reset-demo`)
  - [ ] Automated Backend Test Suite (Pytest: ledger, payments, idempotency, concurrency, reconciliation, refunds)
  - [ ] Frontend tests (Vitest)
  - [ ] Complete Academic Documentation Suite (`docs/`):
    - [ ] `PROJECT_REPORT.md`
    - [ ] `ARCHITECTURE.md`
    - [ ] `DATABASE.md`
    - [ ] `PAYMENT_FLOWS.md`
    - [ ] `API.md`
    - [ ] `ACCOUNTING.md`
    - [ ] `SECURITY.md`
    - [ ] `TEST_PLAN.md`
    - [ ] `DEMO_SCRIPT.md`
    - [ ] `VIVA_PREPARATION.md`
  - [ ] Comprehensive Root `README.md` with Requirements Traceability Table
