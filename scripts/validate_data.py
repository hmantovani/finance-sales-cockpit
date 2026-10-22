"""Validate relationships and reconcile source and reporting totals with SQL."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from generate_data import OUTPUT, generate


def validate(data: dict) -> dict:
    assert data["meta"]["synthetic"] is True
    assert data == generate(), "Dataset differs from deterministic generator"
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE customers(id TEXT PRIMARY KEY);
        CREATE TABLE products(id TEXT PRIMARY KEY);
        CREATE TABLE orders(id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customers(id), status TEXT);
        CREATE TABLE order_items(order_id TEXT REFERENCES orders(id), product_id TEXT REFERENCES products(id), line_total_cents INTEGER CHECK(line_total_cents >= 0));
        CREATE TABLE invoices(id TEXT PRIMARY KEY, order_id TEXT UNIQUE REFERENCES orders(id), amount_cents INTEGER CHECK(amount_cents >= 0));
        CREATE TABLE payments(id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(id), amount_cents INTEGER CHECK(amount_cents >= 0));
    """)
    db.executemany("INSERT INTO customers VALUES (?)", [(row["id"],) for row in data["customers"]])
    db.executemany("INSERT INTO products VALUES (?)", [(row["id"],) for row in data["products"]])
    db.executemany("INSERT INTO orders VALUES (?, ?, ?)", [(r["id"], r["customer_id"], r["status"]) for r in data["orders"]])
    db.executemany("INSERT INTO order_items VALUES (?, ?, ?)", [(r["order_id"], r["product_id"], r["line_total_cents"]) for r in data["order_items"]])
    db.executemany("INSERT INTO invoices VALUES (?, ?, ?)", [(r["id"], r["order_id"], r["amount_cents"]) for r in data["invoices"]])
    db.executemany("INSERT INTO payments VALUES (?, ?, ?)", [(r["id"], r["invoice_id"], r["amount_cents"]) for r in data["payments"]])
    mismatches = db.execute("""
        SELECT i.id FROM invoices i
        JOIN orders o ON o.id = i.order_id
        JOIN (SELECT order_id, SUM(line_total_cents) AS total FROM order_items GROUP BY order_id) x ON x.order_id = o.id
        WHERE o.status != 'fulfilled' OR i.amount_cents != x.total
    """).fetchall()
    assert not mismatches, f"Invoice totals differ from order items: {mismatches}"
    assert db.execute("SELECT COUNT(*) FROM orders o LEFT JOIN invoices i ON i.order_id=o.id WHERE o.status='fulfilled' AND i.id IS NULL").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM orders o JOIN invoices i ON i.order_id=o.id WHERE o.status!='fulfilled'").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM (SELECT i.id, i.amount_cents, COALESCE(SUM(p.amount_cents),0) paid FROM invoices i LEFT JOIN payments p ON p.invoice_id=i.id GROUP BY i.id) WHERE paid>amount_cents").fetchone()[0] == 0
    invoice_total = db.execute("SELECT COALESCE(SUM(amount_cents),0) FROM invoices").fetchone()[0]
    line_total = db.execute("SELECT COALESCE(SUM(x.line_total_cents),0) FROM order_items x JOIN invoices i ON i.order_id=x.order_id").fetchone()[0]
    assert invoice_total == line_total
    return {"customers": len(data["customers"]), "products": len(data["products"]),
            "orders": len(data["orders"]), "invoices": len(data["invoices"]),
            "payments": len(data["payments"]), "invoice_total_cents": invoice_total,
            "invoiced_item_total_cents": line_total}


if __name__ == "__main__":
    report = validate(json.loads(Path(OUTPUT).read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
