# Cockpit questions and metric definitions

## Audience and decisions

The primary user is an owner or operations manager of a small business that sells stocked products on invoice. This cockpit helps them decide which customers to follow up, which orders need attention, and whether cash collection is keeping pace with sales.

1. How much invoiced sales occurred in the selected period?
2. Are sales and cash collections moving together month by month?
3. Which customers and products contribute most to invoiced sales?
4. How much is still open on invoices issued in the selected period?
5. Which open invoices are already overdue, and for how long?
6. Which processing orders have passed their expected fulfillment date?

## Rules

All amounts are BRL, stored as integer cents, displayed as reais. The data snapshot is fixed at **2026-10-22**. Dates are calendar dates in the business's local time. The selected period uses inclusive start and end dates. Cancelled and processing orders are excluded from invoiced sales.

- **Invoiced sales:** sum of invoice amounts whose `issue_date` is within the selected period. One invoice per fulfilled order in this demo. Discounts are already reflected in each order item's `line_total_cents`.
- **Collected cash:** sum of payments whose `payment_date` is within the selected period, regardless of when the related invoice was issued. This is a cash flow measure and need not equal invoiced sales.
- **Open receivables:** for invoices issued within the selected period, invoice amount less payments received on or before the snapshot date. Future dated payments do not reduce the balance.
- **Overdue receivables:** open balance on selected invoices with `due_date` before the snapshot date. An invoice due on the snapshot date is not overdue.
- **Aging buckets:** overdue open balance grouped by calendar days past due: 1–30, 31–60, 61–90, and 91+.
- **Stalled orders:** processing orders placed in the selected period with `expected_fulfillment_date` before the snapshot date. Cancelled orders are excluded.
- **Sales by customer or product:** allocate each invoiced order's item line totals to its customer or product. Their grand totals must equal invoiced sales.

## Controls and details

The date range controls invoiced sales, selected invoice balances, and selected orders by issue or order date respectively. Cash collection uses payment date. Customer filter applies to all measures through the related order. Product filter limits sales to matching invoice lines; cash, invoice balances, and orders remain customer level because payments and invoices are not allocated to individual products. The interface explains this when a product is selected. Invoice detail includes due date, balance, days late, and customer. Sales tables show customer and product contributions. An order queue shows stalled processing orders.
