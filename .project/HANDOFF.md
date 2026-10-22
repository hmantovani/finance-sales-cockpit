# Current state

The finance and sales cockpit MVP is complete. All four initial tasks are done. It uses a fixed, clearly labeled synthetic snapshot dated 2026-10-22.

## What works

- Run `python -m http.server 8000` from the project root and open `http://localhost:8000/dist/`.
- The responsive browser dashboard shows invoiced sales, collected cash, overdue receivables, stalled orders, monthly trends, aging, invoice and order queues, and customer/product sales rankings.
- Date and customer filters apply throughout. Product selection narrows sales only; the interface explains why invoice and cash balances remain customer level.
- The generator reproduces the tracked dataset. SQLite validation reconciles invoiced item totals with invoice totals.
- Python and Node tests pass; a local browser visual pass and customer-filter interaction passed.

## Next steps

1. Plan T-0005 by selecting the additional operational cases for the next release.
2. Review the dashboard and decide whether the portfolio presentation needs a deployment or additional polish.

## Gotchas

- Data is fictional and fixed at 2026-10-22; it is not live financial information.
- Serve over HTTP because the dashboard loads JSON with `fetch`.
- No remote is configured in this local-only Git repository.
