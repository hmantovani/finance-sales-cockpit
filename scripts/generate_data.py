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
    locations = [
        ("São Paulo", "Southeast"), ("Campinas", "Southeast"),
        ("Rio de Janeiro", "Southeast"), ("Belo Horizonte", "Southeast"),
        ("Curitiba", "South"), ("Porto Alegre", "South"),
        ("Brasília", "Central"), ("Goiânia", "Central"),
    ]
    sales_reps = [
        {"id": "R01", "name": "Marina Costa"},
        {"id": "R02", "name": "Lucas Almeida"},
        {"id": "R03", "name": "Beatriz Nunes"},
        {"id": "R04", "name": "Rafael Lima"},
    ]
    customers = [
        {"id": f"C{i:03}", "name": name, "segment": segment,
         "city": locations[(i - 1) % len(locations)][0],
         "region": locations[(i - 1) % len(locations)][1],
         "payment_terms_days": terms}
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
         "unit_price_cents": money(price), "unit_cost_cents": money(cost),
         "opening_stock": stock, "reorder_point": reorder}
        for i, (name, category, price, cost, stock, reorder) in enumerate([
            ("Café premium 1 kg", "Pantry", 78, 46, 260, 35),
            ("Chá seleção", "Pantry", 42, 22, 210, 30),
            ("Copo térmico", "Equipment", 89, 48, 230, 30),
            ("Filtro industrial", "Equipment", 180, 104, 165, 25),
            ("Papel A4 caixa", "Office", 138, 91, 240, 35),
            ("Caneta pack", "Office", 54, 29, 220, 30),
            ("Organizador", "Office", 112, 65, 220, 30),
            ("Kit limpeza", "Supplies", 96, 58, 210, 30),
        ], 1)
    ]
    stock_on_hand = {product["id"]: product["opening_stock"] for product in products}
    orders, order_items, invoice_lines, invoices, installments = [], [], [], [], []
    payments, payment_allocations, returns, credit_notes, refunds, inventory_movements = [], [], [], [], [], []
    start = date(2026, 1, 5)
    for number in range(1, 121):
        placed = start + timedelta(days=int((number - 1) * 2.35) + rng.randrange(2))
        customer = rng.choice(customers)
        cancelled = number % 23 == 0
        held = number % 13 == 0
        expected = placed + timedelta(days=rng.randint(4, 12))
        order_id = f"O{number:04}"
        chosen = rng.sample(products, rng.randint(1, 3))
        order_lines = []
        for index, product in enumerate(chosen, 1):
            qty = rng.randint(2, 15)
            discount = rng.choice([0, 0, 0, 5, 10])
            line = round(qty * product["unit_price_cents"] * (100 - discount) / 100)
            planned = max(1, qty - 2) if number % 17 == 0 and index == 1 else qty
            fulfilled = 0 if cancelled or held else min(planned, stock_on_hand[product["id"]])
            item = {"id": f"OI{number:04}-{index}", "order_id": order_id,
                    "product_id": product["id"], "quantity": qty,
                    "fulfilled_quantity": fulfilled, "unit_price_cents": product["unit_price_cents"],
                    "discount_percent": discount, "line_total_cents": line}
            order_items.append(item)
            if fulfilled:
                stock_on_hand[product["id"]] -= fulfilled
                inventory_movements.append({"id": f"IM{number:04}-{index}",
                                            "product_id": product["id"], "order_id": order_id,
                                            "return_id": None, "date": (placed + timedelta(days=1)).isoformat(),
                                            "quantity_delta": -fulfilled, "reason": "fulfillment"})
                order_lines.append((item, product))
        fulfilled_count = sum(item["fulfilled_quantity"] for item in order_items if item["order_id"] == order_id)
        ordered_count = sum(item["quantity"] for item in order_items if item["order_id"] == order_id)
        status = ("cancelled" if cancelled else "processing" if not fulfilled_count else
                  "fulfilled" if fulfilled_count == ordered_count else "partially_fulfilled")
        orders.append({"id": order_id, "customer_id": customer["id"],
                       "sales_rep_id": sales_reps[(number - 1) % len(sales_reps)]["id"],
                       "order_date": placed.isoformat(), "status": status,
                       "cancellation_reason": rng.choice(["customer_request", "duplicate_order", "credit_hold"]) if cancelled else None,
                       "expected_fulfillment_date": expected.isoformat()})
        if not order_lines:
            continue
        invoice_date = placed + timedelta(days=2)
        due = invoice_date + timedelta(days=customer["payment_terms_days"])
        invoice_id = f"I{number:04}"
        shipping = money(12 + 3 * len(order_lines))
        merchandise = sum(round(item["fulfilled_quantity"] * item["unit_price_cents"] *
                                (100 - item["discount_percent"]) / 100) for item, _ in order_lines)
        allocated_shipping = 0
        line_rows = []
        for index, (item, product) in enumerate(order_lines, 1):
            line_merchandise = round(item["fulfilled_quantity"] * item["unit_price_cents"] *
                                     (100 - item["discount_percent"]) / 100)
            tax = round(line_merchandise * 0.08)
            line_shipping = (shipping - allocated_shipping if index == len(order_lines)
                             else round(shipping * line_merchandise / merchandise))
            allocated_shipping += line_shipping
            line_row = {"id": f"IL{number:04}-{index}", "invoice_id": invoice_id,
                        "order_item_id": item["id"], "product_id": product["id"],
                        "quantity": item["fulfilled_quantity"],
                        "merchandise_cents": line_merchandise, "tax_cents": tax,
                        "shipping_cents": line_shipping,
                        "cost_cents": item["fulfilled_quantity"] * product["unit_cost_cents"],
                        "amount_cents": line_merchandise + tax + line_shipping}
            line_rows.append(line_row)
            invoice_lines.append(line_row)
        total = sum(row["amount_cents"] for row in line_rows)
        invoices.append({"id": invoice_id, "order_id": order_id,
                         "issue_date": invoice_date.isoformat(), "due_date": due.isoformat(),
                         "merchandise_cents": merchandise,
                         "tax_cents": sum(row["tax_cents"] for row in line_rows),
                         "shipping_cents": shipping, "amount_cents": total})
        installment_count = 2 if number % 5 == 0 else 1
        first_amount = total // 2 if installment_count == 2 else total
        installments.append({"id": f"INS{number:04}-1", "invoice_id": invoice_id,
                             "due_date": due.isoformat(), "amount_cents": first_amount})
        if installment_count == 2:
            installments.append({"id": f"INS{number:04}-2", "invoice_id": invoice_id,
                                 "due_date": (due + timedelta(days=30)).isoformat(),
                                 "amount_cents": total - first_amount})
        if number % 7 != 0:
            target = total // 2 if number % 11 == 0 else total
            chunks = [target // 2, target - target // 2] if installment_count == 2 else [target]
            for part, amount in enumerate(chunks, 1):
                pay_date = due + timedelta(days=(part - 1) * 30 + rng.randint(-9, 16))
                if pay_date > AS_OF:
                    continue
                payment_id = f"PM{number:04}-{part}"
                payments.append({"id": payment_id, "invoice_id": invoice_id,
                                 "payment_date": pay_date.isoformat(), "amount_cents": amount,
                                 "method": rng.choice(["bank_transfer", "card", "boleto"])})
                allocated = 0
                for line_index, row in enumerate(line_rows, 1):
                    share = (amount - allocated if line_index == len(line_rows)
                             else round(amount * row["amount_cents"] / total))
                    allocated += share
                    payment_allocations.append({"payment_id": payment_id,
                                                "invoice_line_id": row["id"], "amount_cents": share})
        invoice_credits = []
        if number % 19 == 0:
            line = line_rows[0]
            return_date = invoice_date + timedelta(days=24)
            if return_date <= AS_OF:
                qty = min(2, line["quantity"])
                restockable = number % 38 != 0
                return_id = f"RET{number:04}"
                returned_merchandise = round(line["merchandise_cents"] * qty / line["quantity"])
                returned_tax = round(line["tax_cents"] * qty / line["quantity"])
                returns.append({"id": return_id, "invoice_line_id": line["id"],
                                "return_date": return_date.isoformat(), "quantity": qty,
                                "reason": "damaged" if not restockable else "customer_change",
                                "restockable": restockable})
                credit = {"id": f"CN{number:04}-R", "invoice_id": invoice_id,
                          "invoice_line_id": line["id"], "return_id": return_id,
                          "type": "return", "issue_date": return_date.isoformat(),
                          "merchandise_cents": returned_merchandise, "tax_cents": returned_tax,
                          "shipping_cents": 0,
                          "amount_cents": returned_merchandise + returned_tax}
                credit_notes.append(credit)
                invoice_credits.append(credit)
                if restockable:
                    inventory_movements.append({"id": f"IMRET{number:04}",
                                                "product_id": line["product_id"], "order_id": None,
                                                "return_id": return_id, "date": return_date.isoformat(),
                                                "quantity_delta": qty, "reason": "return_restock"})
        if number % 29 == 0:
            adjustment_date = invoice_date + timedelta(days=20)
            if adjustment_date <= AS_OF:
                line = line_rows[-1]
                credit = {"id": f"CN{number:04}-P", "invoice_id": invoice_id,
                          "invoice_line_id": line["id"], "return_id": None,
                          "type": "price_adjustment", "issue_date": adjustment_date.isoformat(),
                          "merchandise_cents": round(line["merchandise_cents"] * 0.05),
                          "tax_cents": 0, "shipping_cents": 0,
                          "amount_cents": round(line["merchandise_cents"] * 0.05)}
                credit_notes.append(credit)
                invoice_credits.append(credit)
        if number % 31 == 0 or number == 42:
            adjustment_date = invoice_date + timedelta(days=21)
            if adjustment_date <= AS_OF:
                line = line_rows[0]
                amount = min(money(5), line["shipping_cents"])
                credit = {"id": f"CN{number:04}-S", "invoice_id": invoice_id,
                          "invoice_line_id": line["id"], "return_id": None,
                          "type": "shipping_adjustment", "issue_date": adjustment_date.isoformat(),
                          "merchandise_cents": 0, "tax_cents": 0, "shipping_cents": amount,
                          "amount_cents": amount}
                credit_notes.append(credit)
                invoice_credits.append(credit)
        if invoice_credits:
            received = sum(row["amount_cents"] for row in payments if row["invoice_id"] == invoice_id)
            adjusted_total = total - sum(row["amount_cents"] for row in invoice_credits)
            excess = max(0, received - adjusted_total)
            if excess:
                latest_payment = max(date.fromisoformat(row["payment_date"]) for row in payments if row["invoice_id"] == invoice_id)
                latest_credit = max(date.fromisoformat(row["issue_date"]) for row in invoice_credits)
                refund_date = max(latest_payment, latest_credit) + timedelta(days=2)
                if refund_date <= AS_OF:
                    refunds.append({"id": f"RF{number:04}", "invoice_id": invoice_id,
                                    "credit_note_id": invoice_credits[-1]["id"],
                                    "refund_date": refund_date.isoformat(), "amount_cents": excess})
    return {"meta": {"synthetic": True, "seed": SEED, "as_of": AS_OF.isoformat(),
                     "currency": "BRL", "illustrative_tax_percent": 8,
                     "description": "Portfolio demonstration data; no client records."},
            "customers": customers, "sales_reps": sales_reps, "products": products,
            "orders": orders, "order_items": order_items, "invoice_lines": invoice_lines,
            "invoices": invoices, "installments": installments,
            "payments": payments, "payment_allocations": payment_allocations,
            "returns": returns, "credit_notes": credit_notes, "refunds": refunds,
            "inventory_movements": inventory_movements}


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(generate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
