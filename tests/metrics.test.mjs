import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { analyze } from '../dist/metrics.js';

const data = JSON.parse(readFileSync(new URL('../dist/data.json', import.meta.url)));
const all = { start: '2026-01-01', end: data.meta.as_of };

test('sales reconcile to invoices and both drill-downs', () => {
  const result = analyze(data, all);
  assert.equal(result.sales, data.invoices.reduce((sum, row) => sum + row.amount_cents, 0));
  assert.equal(result.sales, result.customerSales.reduce((sum, row) => sum + row[1], 0));
  assert.equal(result.sales, result.productSales.reduce((sum, row) => sum + row[1], 0));
});

test('cash and open balances reconcile to source payments', () => {
  const result = analyze(data, all);
  assert.equal(result.cash, data.payments.reduce((sum, row) => sum + row.amount_cents, 0));
  assert.equal(result.open, result.invoiceRows.reduce((sum, row) => sum + row.balance_cents, 0));
  assert.equal(result.overdue, result.aging.reduce((sum, value) => sum + value, 0));
  assert.ok(result.overdueRows.length > 0);
  assert.ok(result.stalled.length > 0);
});

test('customer and product filters follow their defined scope', () => {
  const customer = data.customers[0].id, product = data.products[0].id;
  const customerOnly = analyze(data, { ...all, customer });
  const both = analyze(data, { ...all, customer, product });
  assert.ok(both.sales <= customerOnly.sales);
  assert.equal(both.cash, customerOnly.cash);
  assert.equal(both.open, customerOnly.open);
  assert.equal(both.stalled.length, customerOnly.stalled.length);
});

test('a date range with no transactions returns empty results', () => {
  const result = analyze(data, { start: '2025-01-01', end: '2025-12-31' });
  assert.equal(result.sales, 0);
  assert.equal(result.cash, 0);
  assert.equal(result.overdue, 0);
  assert.equal(result.stalled.length, 0);
});
