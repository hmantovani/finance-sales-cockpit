"""Create a deterministic, wholly synthetic small-business dataset."""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "data.json"
AS_OF = date(2026, 10, 22)
SEED = 1427


def money(value: float) -> int:
    """Store money as integer cents."""
    return round(value * 100)


def generate() -> dict:
    rng = random.Random(SEED)
    cities = ["São Paulo", "Campinas", "Santos", "Sorocaba", "Ribeirão Preto"]
    customers = [
        {"id": f"C{i:03}", "name": name, "segment": segment,
         "city": cities[(i - 1) % len(cities)], "payment_terms_days": terms}
        for i, (name, segment, terms) in enumerate([
            ("Acme Comércio", "Retail", 30), ("Norte Distribuição", "Wholesale", 45),
            ("Verde Café", "Hospitality", 30), ("Aurora Papelaria", "Retail", 15),
            ("Ponto Central", "Retail", 30), ("Delta Serviços", "Services", 45),
            ("Sol Nascente", "Hospitality", 30), ("Vértice Office", "Wholesale", 30),
            ("Bela Vista", "Retail", 15), ("Lumen Mercado", "Retail", 30),
            ("Estação 12", "Hospitality", 45), ("Nova Forma", "Services", 30),
        ], 1)
    ]
    products = [
        {"id": f"P{i:03}", "name": name, "category": category,
         "unit_price_cents": money(price), "unit_cost_cents": money(cost)}
        for i, (name, category, price, cost) in enumerate([
            ("Café premium 1 kg", "Pantry", 78, 46), ("Chá seleção", "Pantry", 42, 22),
            ("Copo térmico", "Equipment", 89, 48), ("Filtro industrial", "Equipment", 180, 104),
            ("Papel A4 caixa", "Office", 138, 91), ("Caneta pack", "Office", 54, 29),
            ("Organizador", "Office", 112, 65), ("Kit limpeza", "Supplies", 96, 58),
        ], 1)
    ]
    orders, order_items, invoices, payments = [], [], [], []
    start = date(2026, 1, 5)
    for number in range(1, 121):
        placed = start + timedelta(days=rng.randrange((AS_OF - start).days - 4))
        customer = rng.choice(customers)
        status = "cancelled" if number % 23 == 0 else "processing" if number % 13 == 0 else "fulfilled"
        expected = placed + timedelta(days=rng.randint(4, 12))
        order_id = f"O{number:04}"
        orders.append({"id": order_id, "customer_id": customer["id"],
                       "order_date": placed.isoformat(), "status": status,
                       "expected_fulfillment_date": expected.isoformat()})
        chosen = rng.sample(products, rng.randint(1, 3))
        total = 0
        for product in chosen:
            qty = rng.randint(2, 15)
            discount = rng.choice([0, 0, 0, 5, 10])
            line = round(qty * product["unit_price_cents"] * (100 - discount) / 100)
            order_items.append({"order_id": order_id, "product_id": product["id"],
                                "quantity": qty, "unit_price_cents": product["unit_price_cents"],
                                "discount_percent": discount, "line_total_cents": line})
            total += line
        if status != "fulfilled":
            continue
        invoice_date = placed + timedelta(days=rng.randint(1, 7))
        due = invoice_date + timedelta(days=customer["payment_terms_days"])
        invoice_id = f"I{number:04}"
        invoices.append({"id": invoice_id, "order_id": order_id,
                         "issue_date": invoice_date.isoformat(), "due_date": due.isoformat(),
                         "amount_cents": total})
        if number % 7 == 0:
            continue  # intentionally unpaid
        fraction = 0.5 if number % 11 == 0 else 1
        amount = round(total * fraction)
        pay_date = invoice_date + timedelta(days=rng.randint(3, customer["payment_terms_days"] + 18))
        if pay_date <= AS_OF:
            payments.append({"id": f"PM{number:04}", "invoice_id": invoice_id,
                             "payment_date": pay_date.isoformat(), "amount_cents": amount,
                             "method": rng.choice(["bank_transfer", "card", "boleto"])})
    return {"meta": {"synthetic": True, "seed": SEED, "as_of": AS_OF.isoformat(),
                     "currency": "BRL", "description": "Portfolio demonstration data; no client records."},
            "customers": customers, "products": products, "orders": orders,
            "order_items": order_items, "invoices": invoices, "payments": payments}


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(generate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
