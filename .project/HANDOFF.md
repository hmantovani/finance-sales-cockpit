# Current state

The finance and sales cockpit is complete through T-0005. All five project tasks are done. It is a local static browser demo with a fixed synthetic snapshot dated 2026-10-22. No Git remote is configured and nothing has been published.

## What works

- Run `python -m http.server 8000` from the project root and open `http://localhost:8000/dist/`.
- The dashboard shows net merchandise sales, net cash, installment-aware receivables, overdue invoices, stalled/partial orders, returns, credits, refunds, margin, and low-stock products.
- Filters cover dates, customer, product, region, and sales representative. Rankings show customer, product, representative, and region sales.
- The deterministic generator reproduces `dist/data.json`. SQLite-backed validation checks relationships and reconciliations; Python and Node tests pass. The expanded dashboard rendered in a local browser preview.
- See `docs/expansion-scope.md`, `docs/data-model.md`, `docs/metrics.md`, and the in-app `dist/methodology.html` for model rules.

## Next steps

1. Review the expanded dashboard and decide whether to polish the portfolio narrative or visual design.
2. When ready, create the planned GitHub repository and choose a static host such as GitHub Pages. The `dist/` directory is self-contained.

## Gotchas

- All records are fictional; the tax rate is illustrative. This is not a live ERP, accounting system, or claimed business result.
- Serve over HTTP because the dashboard loads JSON with `fetch`.
- Product filtering narrows product-level sales/margin/credits/stock, while cash and balances remain invoice-level; the interface explains the scope.
- No remote is configured in this local-only Git repository.
