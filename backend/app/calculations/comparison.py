"""Compare complete estimates, never pretend partial subtotals are whole scenarios."""

from decimal import localcontext

from .engine import calculate


def compare_estimates(baseline: dict, scenario: dict) -> dict:
    before, after = calculate(baseline), calculate(scenario)
    differences = {}
    with localcontext() as context:
        context.prec = 40
        for key in (
            "installed_power",
            "monthly_energy",
            "annual_energy",
            "monthly_cost",
            "annual_cost",
        ):
            unknown = "unknown_load_ids" if key == "installed_power" else "energy_unknown_load_ids"
            a, b = before.get(key), after.get(key)
            differences[key] = (
                {"value": b["value"] - a["value"], "unit": b["unit"], "status": "estimated"}
                if a is not None and b is not None and not before[unknown] and not after[unknown]
                else None
            )
    return {"baseline": before, "scenario": after, "differences": differences}
