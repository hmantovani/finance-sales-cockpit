"""Validate synthetic source relationships and reconcile financial and stock facts."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from generate_data import OUTPUT, generate


def totals_by(rows: list[dict], key: str, amount: str = "amount_cents") -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for row in rows:
        totals[row[key]] += row[amount]
    return totals


def validate(data: dict) -> dict:
    assert data["meta"]["synthetic"] is True
    assert data == generate(), "Dataset differs from deterministic generator"
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE customers(id TEXT PRIMARY KEY);
        CREATE TABLE sales_reps(id TEXT PRIMARY KEY);
        CREATE TABLE products(id TEXT PRIMARY KEY, opening_stock INTEGER CHECK(opening_stock >= 0));
        CREATE TABLE orders(id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customers(id),
            rep_id TEXT REFERENCES sales_reps(id), status TEXT);
        CREATE TABLE order_items(id TEXT PRIMARY KEY, order_id TEXT REFERENCES orders(id),
            product_id TEXT REFERENCES products(id), quantity INTEGER, fulfilled INTEGER);
        CREATE TABLE invoices(id TEXT PRIMARY KEY, order_id TEXT UNIQUE REFERENCES orders(id),
            amount_cents INTEGER CHECK(amount_cents > 0));
        CREATE TABLE invoice_lines(id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(id),
            order_item_id TEXT UNIQUE REFERENCES order_items(id), product_id TEXT REFERENCES products(id),
            amount_cents INTEGER CHECK(amount_cents > 0));
        CREATE TABLE installments(id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(id), amount_cents INTEGER);
        CREATE TABLE payments(id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(id), amount_cents INTEGER);
        CREATE TABLE payment_allocations(payment_id TEXT REFERENCES payments(id),
            invoice_line_id TEXT REFERENCES invoice_lines(id), amount_cents INTEGER);
        CREATE TABLE returns(id TEXT PRIMARY KEY, invoice_line_id TEXT REFERENCES invoice_lines(id), quantity INTEGER);
        CREATE TABLE credit_notes(id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(id),
            invoice_line_id TEXT REFERENCES invoice_lines(id), return_id TEXT REFERENCES returns(id), amount_cents INTEGER);
        CREATE TABLE refunds(id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(id),
            credit_note_id TEXT REFERENCES credit_notes(id), amount_cents INTEGER);
        CREATE TABLE inventory_movements(id TEXT PRIMARY KEY, product_id TEXT REFERENCES products(id),
            order_id TEXT REFERENCES orders(id), return_id TEXT REFERENCES returns(id), quantity_delta INTEGER);
    """)
    db.executemany("INSERT INTO customers VALUES (?)", [(r["id"],) for r in data["customers"]])
    db.executemany("INSERT INTO sales_reps VALUES (?)", [(r["id"],) for r in data["sales_reps"]])
    db.executemany("INSERT INTO products VALUES (?, ?)", [(r["id"], r["opening_stock"]) for r in data["products"]])
    db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", [(r["id"], r["customer_id"], r["sales_rep_id"], r["status"]) for r in data["orders"]])
    db.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", [(r["id"], r["order_id"], r["product_id"], r["quantity"], r["fulfilled_quantity"]) for r in data["order_items"]])
    db.executemany("INSERT INTO invoices VALUES (?, ?, ?)", [(r["id"], r["order_id"], r["amount_cents"]) for r in data["invoices"]])
    db.executemany("INSERT INTO invoice_lines VALUES (?, ?, ?, ?, ?)", [(r["id"], r["invoice_id"], r["order_item_id"], r["product_id"], r["amount_cents"]) for r in data["invoice_lines"]])
    db.executemany("INSERT INTO installments VALUES (?, ?, ?)", [(r["id"], r["invoice_id"], r["amount_cents"]) for r in data["installments"]])
    db.executemany("INSERT INTO payments VALUES (?, ?, ?)", [(r["id"], r["invoice_id"], r["amount_cents"]) for r in data["payments"]])
    db.executemany("INSERT INTO payment_allocations VALUES (?, ?, ?)", [(r["payment_id"], r["invoice_line_id"], r["amount_cents"]) for r in data["payment_allocations"]])
    db.executemany("INSERT INTO returns VALUES (?, ?, ?)", [(r["id"], r["invoice_line_id"], r["quantity"]) for r in data["returns"]])
    db.executemany("INSERT INTO credit_notes VALUES (?, ?, ?, ?, ?)", [(r["id"], r["invoice_id"], r["invoice_line_id"], r["return_id"], r["amount_cents"]) for r in data["credit_notes"]])
    db.executemany("INSERT INTO refunds VALUES (?, ?, ?, ?)", [(r["id"], r["invoice_id"], r["credit_note_id"], r["amount_cents"]) for r in data["refunds"]])
    db.executemany("INSERT INTO inventory_movements VALUES (?, ?, ?, ?, ?)", [(r["id"], r["product_id"], r["order_id"], r["return_id"], r["quantity_delta"]) for r in data["inventory_movements"]])

    invoice_lines = totals_by(data["invoice_lines"], "invoice_id")
    installments = totals_by(data["installments"], "invoice_id")
    payments = totals_by(data["payments"], "invoice_id")
    credits = totals_by(data["credit_notes"], "invoice_id")
    refunds = totals_by(data["refunds"], "invoice_id")
    allocations = totals_by(data["payment_allocations"], "payment_id")
    orders = {r["id"]: r for r in data["orders"]}
    items = {r["id"]: r for r in data["order_items"]}
    lines = {r["id"]: r for r in data["invoice_lines"]}
    invoices = {r["id"]: r for r in data["invoices"]}
    credit_notes = {r["id"]: r for r in data["credit_notes"]}
    for item in data["order_items"]:
        assert 0 <= item["fulfilled_quantity"] <= item["quantity"]
    for order in data["orders"]:
        order_items = [item for item in data["order_items"] if item["order_id"] == order["id"]]
        fulfilled = sum(item["fulfilled_quantity"] for item in order_items)
        ordered = sum(item["quantity"] for item in order_items)
        expected_status = ("cancelled" if order["cancellation_reason"] else "processing" if not fulfilled else
                           "fulfilled" if fulfilled == ordered else "partially_fulfilled")
        assert order["status"] == expected_status
        assert (order["id"] in {inv["order_id"] for inv in data["invoices"]}) == (fulfilled > 0)
    for line in data["invoice_lines"]:
        assert line["quantity"] == items[line["order_item_id"]]["fulfilled_quantity"]
        assert line["product_id"] == items[line["order_item_id"]]["product_id"]
        assert line["amount_cents"] == sum(line[field] for field in ("merchandise_cents", "tax_cents", "shipping_cents"))
        assert line["cost_cents"] >= 0
    for invoice in data["invoices"]:
        invoice_id = invoice["id"]
        assert invoice_lines[invoice_id] == installments[invoice_id] == invoice["amount_cents"]
        for field in ("merchandise_cents", "tax_cents", "shipping_cents"):
            assert sum(line[field] for line in data["invoice_lines"] if line["invoice_id"] == invoice_id) == invoice[field]
        assert payments[invoice_id] - refunds[invoice_id] <= invoice["amount_cents"] - credits[invoice_id]
        assert refunds[invoice_id] <= credits[invoice_id]
    for payment in data["payments"]:
        assert allocations[payment["id"]] == payment["amount_cents"]
    for allocation in data["payment_allocations"]:
        payment = next(row for row in data["payments"] if row["id"] == allocation["payment_id"])
        assert lines[allocation["invoice_line_id"]]["invoice_id"] == payment["invoice_id"]
    for credit in data["credit_notes"]:
        assert lines[credit["invoice_line_id"]]["invoice_id"] == credit["invoice_id"]
        assert credit["amount_cents"] == sum(credit[field] for field in ("merchandise_cents", "tax_cents", "shipping_cents"))
        assert credit["type"] == ("return" if credit["return_id"] else credit["type"])
    for returned in data["returns"]:
        assert returned["quantity"] <= lines[returned["invoice_line_id"]]["quantity"]
        assert any(credit["return_id"] == returned["id"] for credit in data["credit_notes"])
    for refund in data["refunds"]:
        assert credit_notes[refund["credit_note_id"]]["invoice_id"] == refund["invoice_id"]
    for product in data["products"]:
        movements = [m for m in data["inventory_movements"] if m["product_id"] == product["id"]]
        assert product["opening_stock"] + sum(m["quantity_delta"] for m in movements) >= 0
    for movement in data["inventory_movements"]:
        assert (movement["reason"] == "return_restock") == bool(movement["return_id"])
    gross = db.execute("SELECT COALESCE(SUM(amount_cents),0) FROM invoices").fetchone()[0]
    line_total = db.execute("SELECT COALESCE(SUM(amount_cents),0) FROM invoice_lines").fetchone()[0]
    assert gross == line_total
    net_merchandise = (sum(r["merchandise_cents"] for r in data["invoice_lines"]) -
                       sum(r["merchandise_cents"] for r in data["credit_notes"]))
    return {"orders": len(data["orders"]), "invoices": len(data["invoices"]),
            "installments": len(data["installments"]), "returns": len(data["returns"]),
            "credits": len(data["credit_notes"]), "refunds": len(data["refunds"]),
            "invoice_total_cents": gross, "invoiced_line_total_cents": line_total,
            "net_merchandise_cents": net_merchandise}


if __name__ == "__main__":
    report = validate(json.loads(Path(OUTPUT).read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
