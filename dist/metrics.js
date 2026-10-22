export const money = cents => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
export const dayDiff = (later, earlier) => Math.round((Date.parse(`${later}T00:00:00Z`) - Date.parse(`${earlier}T00:00:00Z`)) / 86400000);

export function analyze(data, filters) {
  const { start, end, customer = 'all', product = 'all' } = filters;
  const inRange = date => date >= start && date <= end;
  const byId = rows => new Map(rows.map(row => [row.id, row]));
  const customers = byId(data.customers), products = byId(data.products), orders = byId(data.orders);
  const selectedOrder = order => customer === 'all' || order.customer_id === customer;
  const invoices = data.invoices.filter(inv => inRange(inv.issue_date) && selectedOrder(orders.get(inv.order_id)));
  const invoiceIds = new Set(invoices.map(inv => inv.id));
  const paymentsByInvoice = new Map();
  for (const pay of data.payments) {
    if (pay.payment_date > data.meta.as_of) continue;
    paymentsByInvoice.set(pay.invoice_id, (paymentsByInvoice.get(pay.invoice_id) || 0) + pay.amount_cents);
  }
  const invoiceRows = invoices.map(inv => {
    const order = orders.get(inv.order_id);
    const balance = Math.max(0, inv.amount_cents - (paymentsByInvoice.get(inv.id) || 0));
    return { ...inv, customer: customers.get(order.customer_id).name, balance_cents: balance,
      days_late: Math.max(0, dayDiff(data.meta.as_of, inv.due_date)) };
  });
  const overdueRows = invoiceRows.filter(inv => inv.balance_cents > 0 && inv.days_late > 0)
    .sort((a, b) => b.days_late - a.days_late || b.balance_cents - a.balance_cents);
  const collections = data.payments.filter(pay => inRange(pay.payment_date) && pay.payment_date <= data.meta.as_of &&
    (customer === 'all' || orders.get(data.invoices.find(inv => inv.id === pay.invoice_id).order_id).customer_id === customer));
  const salesByCustomer = new Map(), salesByProduct = new Map(), monthlySales = new Map(), monthlyCash = new Map();
  let sales = 0;
  for (const inv of invoices) {
    const order = orders.get(inv.order_id);
    const name = customers.get(order.customer_id).name;
    for (const item of data.order_items.filter(item => item.order_id === order.id && (product === 'all' || item.product_id === product))) {
      sales += item.line_total_cents;
      salesByCustomer.set(name, (salesByCustomer.get(name) || 0) + item.line_total_cents);
      const productName = products.get(item.product_id).name;
      salesByProduct.set(productName, (salesByProduct.get(productName) || 0) + item.line_total_cents);
      const month = inv.issue_date.slice(0, 7);
      monthlySales.set(month, (monthlySales.get(month) || 0) + item.line_total_cents);
    }
  }
  for (const pay of collections) {
    const month = pay.payment_date.slice(0, 7);
    monthlyCash.set(month, (monthlyCash.get(month) || 0) + pay.amount_cents);
  }
  const cash = collections.reduce((sum, pay) => sum + pay.amount_cents, 0);
  const open = invoiceRows.reduce((sum, inv) => sum + inv.balance_cents, 0);
  const overdue = overdueRows.reduce((sum, inv) => sum + inv.balance_cents, 0);
  const stalled = data.orders.filter(order => order.status === 'processing' &&
    inRange(order.order_date) && selectedOrder(order) && order.expected_fulfillment_date < data.meta.as_of)
    .map(order => ({ ...order, customer: customers.get(order.customer_id).name,
      days_late: dayDiff(data.meta.as_of, order.expected_fulfillment_date) }))
    .sort((a, b) => b.days_late - a.days_late);
  const aging = [0, 0, 0, 0];
  for (const inv of overdueRows) aging[inv.days_late <= 30 ? 0 : inv.days_late <= 60 ? 1 : inv.days_late <= 90 ? 2 : 3] += inv.balance_cents;
  const rank = map => [...map].sort((a, b) => b[1] - a[1]);
  return { sales, cash, open, overdue, stalled, aging, invoiceRows, overdueRows,
    customerSales: rank(salesByCustomer), productSales: rank(salesByProduct),
    monthlySales, monthlyCash, invoiceCount: invoiceIds.size };
}
