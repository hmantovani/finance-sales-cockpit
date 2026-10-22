---
id: T-0002
title: Build the synthetic data model and generator
status: done
priority: high
created: 2026-10-22
updated: 2026-10-22
---

Create representative orders, customers, products, invoices, and payment records without using client data.

Completed with the documented six-entity model, deterministic generator, and tracked synthetic snapshot in `dist/data.json`.

Acceptance criteria:

- Documented schemas and relationships for all source entities.
- Repeatable synthetic dataset generation with intentional overdue, unpaid, and stalled-order cases.
- Clear labeling that every record is synthetic or from a public source.
