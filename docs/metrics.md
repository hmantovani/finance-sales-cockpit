# Cockpit questions and metric definitions

## Audience and questions

The primary user is an owner or operations manager of a small business selling stocked products on invoice. The expanded cockpit answers:

1. How much net merchandise was sold after returns and price credits?
2. Are cash collections keeping pace with sales after customer refunds?
3. What gross margin remains after product cost and restockable returns?
4. Which installment balances are overdue, and how old are they?
5. Which orders are partly fulfilled or stalled, and how many units remain?
6. Which products need replenishment, and which reps and regions contribute sales?
7. Which returns, price adjustments, and shipping credits changed results?

## General rules

All values are BRL integer cents. The fictional snapshot is fixed at **2026-10-22**. Date filters are inclusive calendar dates. The illustrative flat tax rate is 8%; this is not jurisdictional tax advice. A single invoice covers the fulfilled portion of an order; unfulfilled units remain on the order. Cancelled orders have a reason and no invoice.

## Sales, cost, and cash

- **Net merchandise sales:** merchandise on invoice lines whose invoice issue date is in the selected period, less merchandise on credit notes whose issue date is in the selected period. The credit can relate to an older invoice. Tax and shipping are excluded. Product, customer, region, and rep filters follow the invoice line's order.
- **Gross margin:** net merchandise sales less product cost on invoice lines issued in the period, plus cost reversed for restockable returns credited in the period. Non-restockable returns do not recover cost. Shipping cost, tax, and overhead are excluded.
- **Gross margin rate:** gross margin divided by net merchandise sales; zero if sales are zero. A narrow period can show a negative sale or margin when credits occur without new invoices.
- **Gross billed:** full invoice amount (merchandise + tax + shipping) for invoices issued in the period.
- **Credits:** full credit-note amount issued in the period, including merchandise, tax, and shipping components. Returns and price/shipping adjustments are separate types.
- **Net cash collected:** payments received in the period less refunds paid in the period. Cash events can relate to invoices from a different period.

## Receivables and installments

Receivables include invoices issued during the selected period and use all payment, credit, and refund events through the snapshot date. For each invoice:

`open = invoice amount - all credits - all payments + all refunds`

The ledger does not allow a negative open amount. Credits are applied to the latest-due installment first. Net payments (payments less refunds) settle the earliest installment first. **Overdue receivables** sum unpaid installment balances with due dates before the snapshot; an installment due on the snapshot is not overdue. Aging groups these balances by 1–30, 31–60, 61–90, and 91+ calendar days. The invoice table shows the earliest still-unpaid overdue installment and its overdue amount. A refund restores the part of payment that a credit made refundable, so it does not incorrectly reopen a fully settled adjusted invoice.

## Fulfillment and inventory

- **Partial order:** at least one ordered unit has been fulfilled and at least one remains. A processing order has no fulfilled units. A cancelled order has no fulfillment.
- **Stalled order:** processing or partly fulfilled, placed in the selected period, and expected fulfillment date before the snapshot. Remaining units are ordered less fulfilled quantities.
- **On-hand stock:** opening units plus all fulfillment and restock movements through the snapshot. **Low stock** means on-hand units are at or below the product's reorder point. Stock is global; customer, region, and rep filters do not narrow it.

## Filters and attribution

Date, customer, region, and representative filters apply to transactions through their orders. The product filter narrows sales, margin, credit notes, and inventory. It does not narrow payments, refunds, receivables, or order status because those facts belong to a whole invoice or order. Payments are allocated across invoice lines in the source data for traceability, but the dashboard does not claim that those allocations identify cash collected for a product.
