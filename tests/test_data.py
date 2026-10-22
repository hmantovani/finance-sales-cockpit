import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_data import OUTPUT, generate  # noqa: E402
from validate_data import validate  # noqa: E402


class DatasetTests(unittest.TestCase):
    def test_snapshot_reproduces_and_reconciles(self):
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        report = validate(data)
        self.assertEqual(report["invoice_total_cents"], report["invoiced_line_total_cents"])
        self.assertEqual(report["net_merchandise_cents"],
                         sum(row["merchandise_cents"] for row in data["invoice_lines"]) -
                         sum(row["merchandise_cents"] for row in data["credit_notes"]))
        self.assertEqual(data, generate())

    def test_exception_scenarios_exist(self):
        data = generate()
        paid = {payment["invoice_id"] for payment in data["payments"]}
        self.assertTrue(any(invoice["id"] not in paid for invoice in data["invoices"]))
        self.assertTrue(any(order["status"] == "processing" and order["expected_fulfillment_date"] < data["meta"]["as_of"] for order in data["orders"]))
        self.assertTrue(any(order["status"] == "cancelled" for order in data["orders"]))
        self.assertTrue(any(order["status"] == "partially_fulfilled" for order in data["orders"]))
        self.assertTrue(any(row["restockable"] for row in data["returns"]))
        self.assertTrue(any(not row["restockable"] for row in data["returns"]))
        self.assertTrue(any(row["type"] == "price_adjustment" for row in data["credit_notes"]))
        self.assertTrue(any(row["type"] == "shipping_adjustment" for row in data["credit_notes"]))
        self.assertTrue(any(row["cancellation_reason"] for row in data["orders"]))
        self.assertTrue(any(row["amount_cents"] for row in data["refunds"]))
        self.assertTrue(any(row["region"] for row in data["customers"]))
        self.assertTrue(any(row["quantity_delta"] < 0 for row in data["inventory_movements"]))


if __name__ == "__main__":
    unittest.main()
