import { analyze, money } from './metrics.js';

const $ = id => document.getElementById(id);
const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const shortDate = value => new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`));
const labelMonth = value => new Intl.DateTimeFormat('en-GB', { month: 'short', timeZone: 'UTC' }).format(new Date(`${value}-01T00:00:00Z`));

function trend(sales, cash) {
  const months = [...new Set([...sales.keys(), ...cash.keys()])].sort();
  if (!months.length) { $('trend-chart').innerHTML = '<div class="empty">No activity in this period.</div>'; return; }
  const values = months.flatMap(month => [sales.get(month) || 0, cash.get(month) || 0]);
  const max = Math.max(1, ...values), min = Math.min(0, ...values);
  const x = index => 46 + index * (610 / Math.max(1, months.length - 1));
  const y = value => 185 - (value - min) / (max - min) * 155;
  const path = values => months.map((month, index) => `${index ? 'L' : 'M'} ${x(index)} ${y(values.get(month) || 0)}`).join(' ');
  const grid = [min, (min + max) / 2, max].map(value => `<line class="chart-grid" x1="46" y1="${y(value)}" x2="665" y2="${y(value)}"/><text class="axis-label" x="2" y="${y(value) + 4}">${Math.round(value / 100000)}k</text>`).join('');
  const labels = months.map((month, index) => `<text class="axis-label" text-anchor="middle" x="${x(index)}" y="211">${labelMonth(month)}</text>`).join('');
  const dots = months.map((month, index) => `<circle class="chart-dot" cx="${x(index)}" cy="${y(sales.get(month) || 0)}" r="3"/>`).join('');
  $('trend-chart').innerHTML = `<svg viewBox="0 0 690 230" role="img" aria-label="Monthly sales and cash collection trends">${grid}<path class="cash-line" d="${path(cash)}"/><path class="sales-line" d="${path(sales)}"/>${dots}${labels}</svg>`;
}

function rankings(id, rows) {
  $(id).innerHTML = rows.length ? rows.map(([name, cents], index) => `<div class="rank-row"><span><span class="number">${String(index + 1).padStart(2, '0')}</span>${escapeHtml(name)}</span><strong>${money(cents)}</strong></div>`).join('') : '<div class="empty">No sales in this period.</div>';
}

function render(data) {
  const start = $('start').value, end = $('end').value;
  if (!start || !end || start > end) {
    $('filter-error').hidden = false;
    $('filter-error').textContent = 'Choose a valid date range. “From” must be on or before “To”.';
    $('dashboard').hidden = true;
    return;
  }
  $('filter-error').hidden = true;
  $('dashboard').hidden = false;
  $('product-note').hidden = $('product').value === 'all';
  const result = analyze(data, {start, end, customer: $('customer').value,
    product: $('product').value, region: $('region').value, rep: $('rep').value});
  $('kpi-sales').textContent = money(result.sales);
  $('kpi-cash').textContent = money(result.cash);
  $('kpi-overdue').textContent = money(result.overdue);
  $('kpi-stalled').textContent = String(result.stalled.length);
  $('kpi-margin').textContent = money(result.margin);
  $('margin-rate').textContent = `${Math.round(result.marginRate * 100)}% of net merchandise sales`;
  $('kpi-credits').textContent = money(result.credits);
  $('credit-detail').textContent = `${result.returnCount} returns · ${money(result.refunds)} refunded`;
  $('kpi-partial').textContent = String(result.partialOrders.length);
  $('kpi-low-stock').textContent = String(result.lowStock.length);
  $('overdue-count').textContent = `${result.overdueRows.length} ${result.overdueRows.length === 1 ? 'invoice needs' : 'invoices need'} attention`;
  $('open-total').textContent = money(result.open);
  $('invoice-count').textContent = `${result.overdueRows.length} ${result.overdueRows.length === 1 ? 'invoice' : 'invoices'}`;
  $('order-count').textContent = `${result.stalled.length} ${result.stalled.length === 1 ? 'order' : 'orders'}`;
  trend(result.monthlySales, result.monthlyCash);
  const maxAge = Math.max(1, ...result.aging);
  $('aging-bars').innerHTML = ['1–30 days', '31–60 days', '61–90 days', '91+ days'].map((label, index) => `<div class="bar-row"><div class="bar-head"><span>${label}</span><strong>${money(result.aging[index])}</strong></div><div class="bar-track"><div class="bar-fill" style="width:${100 * result.aging[index] / maxAge}%"></div></div></div>`).join('');
  $('invoice-table').innerHTML = result.overdueRows.length ? result.overdueRows.map(inv => `<tr><td><strong>${escapeHtml(inv.id)}</strong><small>${escapeHtml(inv.customer)}</small></td><td>${shortDate(inv.installment_balances.find(row => row.balance_cents > 0 && row.due_date < data.meta.as_of).due_date)}</td><td class="late">${inv.days_late} days</td><td class="numeric"><strong>${money(inv.overdue_cents)}</strong></td></tr>`).join('') : '<tr><td class="empty" colspan="4">No overdue installments match these filters.</td></tr>';
  $('order-table').innerHTML = result.stalled.length ? result.stalled.map(order => `<tr><td><strong>${escapeHtml(order.id)}</strong><small>${escapeHtml(order.customer)}</small></td><td>${order.status === 'partially_fulfilled' ? 'Partial' : 'Processing'}</td><td>${order.remaining_units}</td><td class="numeric late">${order.days_late} days</td></tr>`).join('') : '<tr><td class="empty" colspan="4">No stalled orders match these filters.</td></tr>';
  $('adjustment-count').textContent = `${result.adjustmentRows.length} credits`;
  const creditType = { return: 'Return', price_adjustment: 'Price', shipping_adjustment: 'Shipping' };
  $('adjustment-table').innerHTML = result.adjustmentRows.length ? result.adjustmentRows.map(credit => `<tr><td><strong>${escapeHtml(credit.id)}</strong><small>${escapeHtml(credit.customer)} · ${escapeHtml(credit.product)}</small></td><td>${creditType[credit.type]}</td><td>${shortDate(credit.issue_date)}</td><td class="numeric"><strong>${money(credit.amount_cents)}</strong></td></tr>`).join('') : '<tr><td class="empty" colspan="4">No credits in this period.</td></tr>';
  $('stock-count').textContent = `${result.lowStock.length} low`;
  $('stock-table').innerHTML = result.stock.map(row => `<tr><td><strong>${escapeHtml(row.name)}</strong><small>${escapeHtml(row.category)}</small></td><td class="${row.low ? 'stock-low' : 'stock-ok'}">${row.on_hand} units</td><td class="numeric">${row.reorder_point} units</td></tr>`).join('');
  rankings('customer-rank', result.customerSales);
  rankings('product-rank', result.productSales);
  rankings('region-rank', result.regionSales);
  rankings('rep-rank', result.repSales);
}

async function init() {
  try {
    const response = await fetch('data.json');
    if (!response.ok) throw new Error(`Data request failed (${response.status})`);
    const data = await response.json();
    for (const customer of data.customers) $('customer').add(new Option(customer.name, customer.id));
    for (const product of data.products) $('product').add(new Option(product.name, product.id));
    for (const region of [...new Set(data.customers.map(row => row.region))].sort()) $('region').add(new Option(region, region));
    for (const rep of data.sales_reps) $('rep').add(new Option(rep.name, rep.id));
    for (const id of ['start', 'end', 'customer', 'product', 'region', 'rep']) $(id).addEventListener('change', () => render(data));
    $('reset').addEventListener('click', () => { for (const id of ['customer', 'product', 'region', 'rep']) $(id).value = 'all'; $('start').value = '2026-01-01'; $('end').value = data.meta.as_of; render(data); });
    $('loading').hidden = true;
    render(data);
  } catch (error) {
    $('loading').textContent = `Could not load demo data: ${error.message}. Serve the dist directory with a local HTTP server.`;
  }
}
init();
