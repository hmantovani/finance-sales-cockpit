---
id: T-0005
title: Expand the model with operational business cases
status: done
priority: medium
created: 2026-10-22
updated: 2026-10-22
---

Extend the synthetic model and dashboard to cover the additional cases requested after the MVP: returns and refunds, credit notes and invoice adjustments, partial fulfillment, cancellation reasons, taxes and shipping costs, installment payments, sales representatives and regions, inventory and stockouts, purchase costs and gross margin, and payment allocation by invoice line.

Acceptance criteria:

- Agree on the cases for the next release and document the scope before changing schemas.
- Update the data model, generator, metric rules, validations, tests, and dashboard views for the selected cases.
- Keep all records synthetic and preserve reconciliation from source facts to displayed KPIs.
- Update the README with the new business questions and known modeling limits.

Scope selected for this release: all listed cases, implemented as a compact synthetic demonstration with a flat illustrative tax rate, one invoice for the fulfilled portion of each order, and traceable line-level payment allocations.

Completed 2026-10-22. The generator, validation, metric engine, dashboard, documentation, and tests now cover all selected cases. See `docs/expansion-scope.md` for assumptions and limits.
