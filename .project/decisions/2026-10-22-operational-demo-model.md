# Operational demo model

Date: 2026-10-22

Decision: Include all ten requested operational cases in one synthetic, fixed-snapshot release. Use one invoice for the fulfilled quantity of each order, illustrative flat tax, shipping charges without shipping expense, installment due dates, line-level payment traceability, and a stock movement ledger. Net merchandise sales exclude tax and shipping; cash is payments less refunds; receivables are installment balances after credits and net payments.

Rationale: This gives the portfolio case a coherent operational story while keeping every displayed KPI reconcilable to source facts. The simplifications and filter scopes are documented in `docs/expansion-scope.md` and `docs/metrics.md`.
