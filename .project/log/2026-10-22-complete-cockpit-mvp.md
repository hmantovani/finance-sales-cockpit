---
date: 2026-10-22
agent: codex
status: done
type: feature
tasks: [T-0001, T-0002, T-0003, T-0004]
title: Complete finance and sales cockpit MVP
---

## Goal

Complete all four initial project tasks: KPI design, synthetic data, browser dashboard, and quality/documentation.

## Discussion

The user requested completion of all open tasks. The delivery stays within the project's local-only Git policy. The first release uses a fictional business and fixed date to keep the portfolio demonstration reproducible.

## What changed

- Defined six business questions, all KPI rules, and filter scope in `docs/metrics.md`.
- Added a six-entity synthetic data model, seeded generator, and 120-order snapshot.
- Built a responsive browser dashboard with filters, trends, aging, exception queues, and sales drill-downs.
- Added SQLite reconciliation, six automated tests, README walkthrough, and architecture/data-model diagrams.
- Marked T-0001 through T-0004 done and rewrote the handoff.
- Commits: `9ccf388 feat: build synthetic finance and sales cockpit`; final `.project/` metadata commit `docs: close cockpit MVP tasks`.

## Verification

- Python dataset validation: 106 invoices totaling 17,854,565 cents, equal to invoiced order-item totals.
- Two Python tests and four Node tests passed.
- Local HTTP responses for the page and JSON returned 200; browser visual and customer-filter checks passed.

## Next steps

Review the dashboard presentation and decide whether to deploy or expand its model in a new task.
