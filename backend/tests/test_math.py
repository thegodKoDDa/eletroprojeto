"""Runnable with unittest or pytest, without third-party dependencies.

Expected values derive from explicit arithmetic examples, not normative claims.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from decimal import Decimal as D

from app.calculations.current import current_from_active
from app.calculations.engine import calculate
from app.calculations.power import apparent_power, installed_power, watts_to_kw


def fixture():
    return {
        "utility": "energisa_sul_sudeste",
        "environments": [
            {
                "id": "room-1",
                "loads": [
                    {
                        "id": "load-1",
                        "name": "Chuveiro",
                        "category": "Aquecimento",
                        "kind": "specific_use",
                        "unit_power_w": "7500",
                        "quantity": 2,
                        "power_factor": "1",
                        "power_origin": "nameplate",
                        "source": "Exemplo aritmético",
                        "demand_classification": None,
                    },
                    {
                        "id": "load-2",
                        "name": "LED",
                        "category": "Iluminação",
                        "kind": "lighting",
                        "unit_power_w": "9",
                        "quantity": 4,
                        "power_factor": "0.9",
                        "power_origin": "user_estimate",
                        "source": "Exemplo aritmético",
                        "demand_classification": None,
                    },
                ],
            }
        ],
    }


class PowerTests(unittest.TestCase):
    def test_two_showers(self):
        self.assertEqual(installed_power(2, D(7500)), D(15000))

    def test_four_leds(self):
        self.assertEqual(installed_power(4, D(9)), D(36))

    def test_decimal_precision(self):
        self.assertEqual(installed_power(3, D("0.1")), D("0.3"))

    def test_conversion(self):
        self.assertEqual(watts_to_kw(D("1536.5")), D("1.5365"))

    def test_apparent_power(self):
        self.assertEqual(apparent_power(D(900), D("0.9")), D(1000))

    def test_invalid_quantities(self):
        for quantity in (0, -1, 1.2, True):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                installed_power(quantity, D(1))

    def test_invalid_power(self):
        for power in ("-1", "NaN", "Infinity"):
            with self.subTest(power=power), self.assertRaises(ValueError):
                installed_power(1, D(power))

    def test_zero_power(self):
        self.assertEqual(installed_power(2, D(0)), D(0))

    def test_invalid_pf(self):
        for pf in ("0", "-0.2", "1.01", "NaN"):
            with self.subTest(pf=pf), self.assertRaises(ValueError):
                apparent_power(D(100), D(pf))

    def test_single_phase(self):
        self.assertEqual(current_from_active(D(2200), D(220), D(1), "single_phase"), D(10))

    def test_non_unity_pf(self):
        self.assertEqual(current_from_active(D(1760), D(220), D("0.8"), "single_phase"), D(10))

    def test_balanced_three_phase(self):
        actual = current_from_active(D(6600), D(220), D(1), "balanced_three_phase")
        self.assertLess(abs(actual - D("17.3205080756887729352744634151")), D("1e-25"))

    def test_reject_unknown_topology(self):
        with self.assertRaises(ValueError):
            current_from_active(D(100), D(220), D(1), "two_phase")

    def test_reject_zero_voltage(self):
        with self.assertRaises(ValueError):
            current_from_active(D(100), D(0), D(1), "single_phase")


class EngineTests(unittest.TestCase):
    def test_totals_no_double_counting(self):
        result = calculate(fixture())
        self.assertEqual(result["installed_power"]["value"], D(15036))
        self.assertEqual(result["lighting_nominal"]["value"], D(36))
        self.assertEqual(result["by_environment_w"]["room-1"], D(15036))
        self.assertEqual(result["by_category_w"]["Aquecimento"], D(15000))
        self.assertEqual(result["apparent_power"]["value"], D(15040))

    def test_normative_values_blocked(self):
        result = calculate(fixture())
        self.assertEqual(result["status"], "estimated")
        self.assertNotIn("normative", result)

    def test_memory(self):
        entry = calculate(fixture())["memory"][0]
        self.assertEqual(entry["inputs"], {"quantity": 2, "unit_power_w": "7500"})
        self.assertEqual(entry["result"], {"value": "15000", "unit": "W"})

    def test_missing_pf_does_not_assume_unity(self):
        data = fixture()
        data["environments"][0]["loads"][0]["power_factor"] = None
        self.assertIsNone(calculate(data)["apparent_power"])

    def test_edit_changes_result_and_digest(self):
        data = fixture()
        before = calculate(data)
        data["environments"][0]["loads"][0]["unit_power_w"] = "5500"
        after = calculate(data)
        self.assertEqual(after["installed_power"]["value"], D(11036))
        self.assertNotEqual(before["input_digest"], after["input_digest"])

    def test_estimated_origin_propagates(self):
        self.assertEqual(calculate(fixture())["installed_power"]["status"], "estimated")

    def test_no_mutation(self):
        import copy

        data = fixture()
        snapshot = copy.deepcopy(data)
        calculate(data)
        self.assertEqual(data, snapshot)

    def test_empty_project(self):
        result = calculate({"utility": "unconfirmed", "environments": []})
        self.assertEqual(result["installed_power"]["value"], D(0))
        self.assertEqual(result["status"], "estimated")


if __name__ == "__main__":
    unittest.main()
