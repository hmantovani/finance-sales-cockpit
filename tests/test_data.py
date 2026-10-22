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
        self.assertEqual(report["invoice_total_cents"], report["invoiced_item_total_cents"])
        self.assertEqual(data, generate())

    def test_exception_scenarios_exist(self):
        data = generate()
        paid = {payment["invoice_id"] for payment in data["payments"]}
        self.assertTrue(any(invoice["id"] not in paid for invoice in data["invoices"]))
        self.assertTrue(any(order["status"] == "processing" and order["expected_fulfillment_date"] < data["meta"]["as_of"] for order in data["orders"]))
        self.assertTrue(any(order["status"] == "cancelled" for order in data["orders"]))


if __name__ == "__main__":
    unittest.main()
