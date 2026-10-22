export const money = cents => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
export const dayDiff = (later, earlier) => Math.round((Date.parse(`${later}T00:00:00Z`) - Date.parse(`${earlier}T00:00:00Z`)) / 86400000);

const sum = (rows, field) => rows.reduce((total, row) => total + row[field], 0);
const byId = rows => new Map(rows.map(row => [row.id, row]));
const rank = map => [...map].sort((a, b) => b[1] - a[1]);
const add = (map, key, amount) => map.set(key, (map.get(key) || 0) + amount);

// Credits reduce the latest due installment first. Net customer payments settle the oldest first.
export function installmentBalances(schedule, credits, netPayments, asOf) {
  const rows = schedule.map(row => ({ ...row, balance_cents: row.amount_cents }))
    .sort((a, b) => a.due_date.localeCompare(b.due_date));
  for (const row of [...rows].reverse()) {
    const applied = Math.min(row.balance_cents, credits);
    row.balance_cents -= applied;
    credits -= applied;
  }
  for (const row of rows) {
    const applied = Math.min(row.balance_cents, netPayments);
    row.balance_cents -= applied;
    netPayments -= applied;
  }
  return {
    rows,
    open: sum(rows, 'balance_cents'),
    overdue: sum(rows.filter(row => row.due_date < asOf), 'balance_cents'),
  };
}

export function analyze(data, filters) {
  const { start, end, customer = 'all', product = 'all', region = 'all', rep = 'all' } = filters;
  const asOf = data.meta.as_of;
  const inRange = date => date >= start && date <= end && date <= asOf;
  const customers = byId(data.customers), products = byId(data.products), reps = byId(data.sales_reps);
  const orders = byId(data.orders), invoicesById = byId(data.invoices), lines = byId(data.invoice_lines);
  const returnsById = byId(data.returns);
  const selectedOrder = order => (customer === 'all' || order.customer_id === customer) &&
    (region === 'all' || customers.get(order.customer_id).region === region) &&
    (rep === 'all' || order.sales_rep_id === rep);
  const selectedLine = line => product === 'all' || line.product_id === product;
  const selectedInvoices = data.invoices.filter(inv => inRange(inv.issue_date) && selectedOrder(orders.get(inv.order_id)));
  const selectedInvoiceIds = new Set(selectedInvoices.map(inv => inv.id));
  const paymentsByInvoice = new Map(), refundsByInvoice = new Map(), creditsByInvoice = new Map();
  for (const payment of data.payments) if (payment.payment_date <= asOf) add(paymentsByInvoice, payment.invoice_id, payment.amount_cents);
  for (const refund of data.refunds) if (refund.refund_date <= asOf) add(refundsByInvoice, refund.invoice_id, refund.amount_cents);
  for (const credit of data.credit_notes) if (credit.issue_date <= asOf) add(creditsByInvoice, credit.invoice_id, credit.amount_cents);
  const invoiceRows = selectedInvoices.map(inv => {
    const order = orders.get(inv.order_id);
    const schedule = data.installments.filter(row => row.invoice_id === inv.id);
    const balances = installmentBalances(schedule, creditsByInvoice.get(inv.id) || 0,
      (paymentsByInvoice.get(inv.id) || 0) - (refundsByInvoice.get(inv.id) || 0), asOf);
    const earliestOverdue = balances.rows.find(row => row.balance_cents > 0 && row.due_date < asOf);
    const nextOpen = balances.rows.find(row => row.balance_cents > 0);
    return { ...inv, customer: customers.get(order.customer_id).name,
      balance_cents: balances.open, overdue_cents: balances.overdue,
      next_due_date: nextOpen?.due_date || inv.due_date,
      days_late: earliestOverdue ? dayDiff(asOf, earliestOverdue.due_date) : 0,
      installment_balances: balances.rows };
  });
  const overdueRows = invoiceRows.filter(inv => inv.overdue_cents > 0)
    .sort((a, b) => b.days_late - a.days_late || b.overdue_cents - a.overdue_cents);
  const customerSales = new Map(), productSales = new Map(), regionSales = new Map(), repSales = new Map();
  const monthlySales = new Map(), monthlyCash = new Map();
  let sales = 0, margin = 0, grossBilled = 0, credits = 0, returnCount = 0;
  for (const inv of selectedInvoices) grossBilled += inv.amount_cents;
  for (const line of data.invoice_lines) {
    const inv = invoicesById.get(line.invoice_id), order = orders.get(inv.order_id);
    if (!inRange(inv.issue_date) || !selectedOrder(order) || !selectedLine(line)) continue;
    recordSales(line.merchandise_cents, inv.issue_date, order, line.product_id);
    margin -= line.cost_cents;
  }
  const adjustmentRows = [];
  for (const credit of data.credit_notes) {
    const line = lines.get(credit.invoice_line_id), inv = invoicesById.get(credit.invoice_id);
    const order = orders.get(inv.order_id);
    if (!inRange(credit.issue_date) || !selectedOrder(order) || !selectedLine(line)) continue;
    credits += credit.amount_cents;
    recordSales(-credit.merchandise_cents, credit.issue_date, order, line.product_id);
    if (credit.return_id) {
      returnCount += 1;
      const returned = returnsById.get(credit.return_id);
      if (returned.restockable) margin += returned.quantity * products.get(line.product_id).unit_cost_cents;
    }
    adjustmentRows.push({ ...credit, customer: customers.get(order.customer_id).name,
      product: products.get(line.product_id).name });
  }
  function recordSales(amount, date, order, productId) {
    sales += amount;
    const buyer = customers.get(order.customer_id);
    add(customerSales, buyer.name, amount);
    add(productSales, products.get(productId).name, amount);
    add(regionSales, buyer.region, amount);
    add(repSales, reps.get(order.sales_rep_id).name, amount);
    add(monthlySales, date.slice(0, 7), amount);
    margin += amount;
  }
  const payments = data.payments.filter(pay => inRange(pay.payment_date) &&
    selectedOrder(orders.get(invoicesById.get(pay.invoice_id).order_id)));
  const refunds = data.refunds.filter(refund => inRange(refund.refund_date) &&
    selectedOrder(orders.get(invoicesById.get(refund.invoice_id).order_id)));
  for (const pay of payments) add(monthlyCash, pay.payment_date.slice(0, 7), pay.amount_cents);
  for (const refund of refunds) add(monthlyCash, refund.refund_date.slice(0, 7), -refund.amount_cents);
  const cash = sum(payments, 'amount_cents') - sum(refunds, 'amount_cents');
  const open = sum(invoiceRows, 'balance_cents'), overdue = sum(overdueRows, 'overdue_cents');
  const aging = [0, 0, 0, 0];
  for (const inv of invoiceRows) for (const installment of inv.installment_balances) {
    if (!installment.balance_cents || installment.due_date >= asOf) continue;
    const days = dayDiff(asOf, installment.due_date);
    aging[days <= 30 ? 0 : days <= 60 ? 1 : days <= 90 ? 2 : 3] += installment.balance_cents;
  }
  const selectedOrders = data.orders.filter(order => inRange(order.order_date) && selectedOrder(order));
  const stalled = selectedOrders.filter(order => ['processing', 'partially_fulfilled'].includes(order.status) &&
    order.expected_fulfillment_date < asOf)
    .map(order => ({ ...order, customer: customers.get(order.customer_id).name,
      days_late: dayDiff(asOf, order.expected_fulfillment_date),
      remaining_units: sum(data.order_items.filter(item => item.order_id === order.id)
        .map(item => ({ remaining: item.quantity - item.fulfilled_quantity })), 'remaining') }))
    .sort((a, b) => b.days_late - a.days_late);
  const partialOrders = selectedOrders.filter(order => order.status === 'partially_fulfilled');
  const cancelledOrders = selectedOrders.filter(order => order.status === 'cancelled');
  const stock = data.products.filter(row => product === 'all' || row.id === product).map(row => {
    const onHand = row.opening_stock + data.inventory_movements
      .filter(movement => movement.product_id === row.id && movement.date <= asOf)
      .reduce((total, movement) => total + movement.quantity_delta, 0);
    return { ...row, on_hand: onHand, low: onHand <= row.reorder_point };
  });
  return { sales, margin, marginRate: sales ? margin / sales : 0, grossBilled,
    cash, credits, refunds: sum(refunds, 'amount_cents'), returnCount,
    open, overdue, stalled, partialOrders, cancelledOrders, stock,
    lowStock: stock.filter(row => row.low), aging, invoiceRows, overdueRows,
    adjustmentRows: adjustmentRows.sort((a, b) => b.issue_date.localeCompare(a.issue_date)),
    customerSales: rank(customerSales), productSales: rank(productSales),
    regionSales: rank(regionSales), repSales: rank(repSales),
    monthlySales, monthlyCash, invoiceCount: selectedInvoiceIds.size };
}
