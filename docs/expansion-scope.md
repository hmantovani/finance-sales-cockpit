# Operational expansion scope

This release adds every case captured in T-0005 to the fictional Northstar demonstration. The purpose is to show linked operational facts and explain their effect on sales, cash, receivables, and margin.

- Orders can be fulfilled, partly fulfilled, processing, or cancelled with a reason. Only fulfilled quantities are invoiced.
- Invoices carry merchandise, illustrative 8% tax, and shipping. Some split into two installments with separate due dates.
- Returns reference an invoice line and generate a credit note. A restockable return adds inventory and reverses its item cost. Non-restockable returns leave that cost in margin.
- Price and shipping adjustments generate credit notes without a return. A refund is paid when credits exceed the unpaid invoice balance after customer payments.
- Every payment has allocations across invoice lines. The allocation supports traceability; cash and receivables remain invoice-level measures.
- Customers have regions and orders have sales representatives. Products have opening stock, a reorder point, and unit cost. Fulfillment and restockable returns create inventory movements.

The dashboard will add net merchandise sales, gross margin, credits, refunds, partial orders, low-stock alerts, an adjustment ledger, and representative/region views. All examples remain synthetic. Tax is illustrative, not a tax calculation for any jurisdiction; shipping revenue and fulfillment overhead are excluded from gross margin.
