import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { analyze, installmentBalances } from '../dist/metrics.js';

const data = JSON.parse(readFileSync(new URL('../dist/data.json', import.meta.url)));
const all = { start: '2026-01-01', end: data.meta.as_of };

test('net merchandise sales and margin reconcile to source and rankings', () => {
  const result = analyze(data, all);
  const merchandise = data.invoice_lines.reduce((sum, row) => sum + row.merchandise_cents, 0);
  const creditMerchandise = data.credit_notes.reduce((sum, row) => sum + row.merchandise_cents, 0);
  const cost = data.invoice_lines.reduce((sum, row) => sum + row.cost_cents, 0);
  const restoredCost = data.returns.filter(row => row.restockable).reduce((sum, row) => {
    const line = data.invoice_lines.find(line => line.id === row.invoice_line_id);
    const product = data.products.find(product => product.id === line.product_id);
    return sum + row.quantity * product.unit_cost_cents;
  }, 0);
  assert.equal(result.sales, merchandise - creditMerchandise);
  assert.equal(result.margin, result.sales - cost + restoredCost);
  assert.equal(result.grossBilled, data.invoices.reduce((sum, row) => sum + row.amount_cents, 0));
  assert.equal(result.sales, result.customerSales.reduce((sum, row) => sum + row[1], 0));
  assert.equal(result.sales, result.productSales.reduce((sum, row) => sum + row[1], 0));
  assert.equal(result.sales, result.regionSales.reduce((sum, row) => sum + row[1], 0));
  assert.equal(result.sales, result.repSales.reduce((sum, row) => sum + row[1], 0));
});

test('cash and open balances reconcile to source payments', () => {
  const result = analyze(data, all);
  assert.equal(result.cash, data.payments.reduce((sum, row) => sum + row.amount_cents, 0) -
    data.refunds.reduce((sum, row) => sum + row.amount_cents, 0));
  assert.equal(result.credits, data.credit_notes.reduce((sum, row) => sum + row.amount_cents, 0));
  assert.equal(result.open, result.invoiceRows.reduce((sum, row) => sum + row.balance_cents, 0));
  assert.equal(result.overdue, result.aging.reduce((sum, value) => sum + value, 0));
  assert.ok(result.overdueRows.length > 0);
  assert.ok(result.stalled.length > 0);
  assert.ok(result.partialOrders.length > 0);
  assert.ok(result.lowStock.length > 0);
  for (const invoice of result.invoiceRows) {
    const credits = data.credit_notes.filter(row => row.invoice_id === invoice.id).reduce((sum, row) => sum + row.amount_cents, 0);
    const payments = data.payments.filter(row => row.invoice_id === invoice.id).reduce((sum, row) => sum + row.amount_cents, 0);
    const refunds = data.refunds.filter(row => row.invoice_id === invoice.id).reduce((sum, row) => sum + row.amount_cents, 0);
    assert.equal(invoice.balance_cents, invoice.amount_cents - credits - payments + refunds);
  }
});

test('installments apply credits latest due and net payments oldest due', () => {
  const rows = [
    { id: 'a', due_date: '2026-01-01', amount_cents: 100 },
    { id: 'b', due_date: '2026-03-01', amount_cents: 100 },
  ];
  const result = installmentBalances(rows, 40, 70, '2026-02-01');
  assert.deepEqual(result.rows.map(row => row.balance_cents), [30, 60]);
  assert.equal(result.open, 90);
  assert.equal(result.overdue, 30);
});

test('customer and product filters follow their defined scope', () => {
  const customer = data.customers[0].id, product = data.products[0].id;
  const customerOnly = analyze(data, { ...all, customer });
  const both = analyze(data, { ...all, customer, product });
  assert.ok(both.sales <= customerOnly.sales);
  assert.equal(both.cash, customerOnly.cash);
  assert.equal(both.open, customerOnly.open);
  assert.equal(both.stalled.length, customerOnly.stalled.length);
  const region = data.customers[0].region;
  const regionOnly = analyze(data, { ...all, region });
  assert.ok(regionOnly.sales <= analyze(data, all).sales);
  const repOnly = analyze(data, { ...all, rep: data.sales_reps[0].id });
  assert.ok(repOnly.invoiceCount > 0);
  const productOnly = analyze(data, { ...all, product });
  assert.equal(productOnly.stock.length, 1);
});

test('a date range with no transactions returns empty results', () => {
  const result = analyze(data, { start: '2025-01-01', end: '2025-12-31' });
  assert.equal(result.sales, 0);
  assert.equal(result.cash, 0);
  assert.equal(result.overdue, 0);
  assert.equal(result.stalled.length, 0);
});
