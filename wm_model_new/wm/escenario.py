# Bloque 1 — docstring del módulo
r"""
escenario.py — scenario selector for scalar parameters
======================================================

This module selects one scenario column from the Excel input workbook and writes
the active scalar-parameter file used by the model.

Expected Excel input
--------------------
Workbook:
    data/model_inputs.xlsx

Sheet:
    params_scalar

Expected columns:
    name | value_0 | value_1 | value_2 | value_3 | note

Scenario logic (revised — education x convenience factorial)
--------------------------------------------------------------
- value_0: education OFF, convenience OFF (no behavioral response)
- value_1: education ON,  convenience OFF
- value_2: education OFF, convenience ON  (formerly "mechanical separation
  of mixed general waste" — that pathway has been retired from the code,
  it does not exist in Miami-Dade's single-stream system; this column was
  repurposed)
- value_3: education ON,  convenience ON  (both together)

Output written
--------------
    data/params_scalar.csv

with columns:
    name | value | note

The rest of the model does not need to know about value_0, value_1, etc.
It only reads the selected active column as the standard `value`.
"""


# Bloque 2 — imports and paths
from __future__ import annotations

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_XLSX = DATA_DIR / "model_inputs.xlsx"
PARAMS_SHEET = "params_scalar"
PARAMS_CSV = DATA_DIR / "params_scalar.csv"


# Bloque 3 — scenario descriptions (revised — education x convenience factorial)
SCENARIO_DESCRIPTIONS = {
    "value_0": {
        "name": "No behavioral response (baseline)",
        "logic": (
            "Generation and sorting driven only by fixed intercepts; awareness "
            "and convenience have no effect. Informal leakage present at its "
            "structural baseline (leakage_H intercept) but not responsive to "
            "policy."
        ),
        "active_mechanisms": (
            "Education OFF; convenience OFF; generation prevention OFF; "
            "mechanical separation retired (n/a)."
        ),
    },
    "value_1": {
        "name": "Education only",
        "logic": (
            "Awareness (built by education spend E_edu) shifts recycling, "
            "organics, and informal-leakage shares. Convenience channel "
            "stays off."
        ),
        "active_mechanisms": (
            "Education ON; convenience OFF."
        ),
    },
    "value_2": {
        "name": "Convenience only",
        "logic": (
            "Convenience stock (built by infrastructure spend X_MUN) shifts "
            "recycling, organics, and informal-leakage shares. Education "
            "channel stays off. NOTE: this column previously encoded "
            "'mechanical separation of mixed general waste' — that "
            "mechanism has been retired from the code (does not exist in "
            "Miami-Dade's single-stream system) and this column has been "
            "repurposed."
        ),
        "active_mechanisms": (
            "Education OFF; convenience ON."
        ),
    },
    "value_3": {
        "name": "Education + convenience",
        "logic": (
            "Both behavioral channels active together — the 'full' "
            "behavioral case."
        ),
        "active_mechanisms": (
            "Education ON; convenience ON."
        ),
    },
}


# Bloque 4 — scenario selector
def aplicar_escenario(
    scenario: str = "value_0",
    xlsx_path: Path | str = DEFAULT_XLSX,
    out_csv: Path | str = PARAMS_CSV,
) -> pd.DataFrame:
    """
    Select one scenario column from model_inputs.xlsx and write params_scalar.csv.

    Parameters
    ----------
    scenario:
        Scenario column to activate. Expected values:
        value_0, value_1, value_2, value_3.

    xlsx_path:
        Path to model_inputs.xlsx.

    out_csv:
        Path where the active params_scalar.csv will be written.

    Returns
    -------
    pandas.DataFrame
        The active parameter table with columns:
        name | value | note
    """
    xlsx_path = Path(xlsx_path)
    out_csv = Path(out_csv)

    if not xlsx_path.exists():
        raise FileNotFoundError(
            f"Cannot apply scenario because Excel input file was not found: {xlsx_path}"
        )

    params = pd.read_excel(xlsx_path, sheet_name=PARAMS_SHEET)

    required = {"name", scenario}
    missing = required - set(params.columns)
    if missing:
        raise ValueError(
            f"Cannot apply scenario '{scenario}'. Missing columns in sheet "
            f"'{PARAMS_SHEET}': {sorted(missing)}"
        )

    active = params[["name", scenario]].copy()
    active = active.rename(columns={scenario: "value"})

    if "note" in params.columns:
        active["note"] = params["note"]
    else:
        active["note"] = ""

    # Drop empty parameter rows.
    active = active.dropna(subset=["name"]).copy()

    # If a selected scenario leaves a value blank, fail clearly.
    missing_values = active[active["value"].isna()]["name"].tolist()
    if missing_values:
        raise ValueError(
            f"Scenario '{scenario}' has missing values for parameters: {missing_values}"
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    active.to_csv(out_csv, index=False, sep=",", decimal=".", encoding="utf-8")

    desc = SCENARIO_DESCRIPTIONS.get(scenario, {})
    print("[escenario] Active scenario selected")
    print(f"  column              : {scenario}")
    print(f"  name                : {desc.get('name', 'not documented')}")
    print(f"  active params written: {out_csv}")
    print(f"  rows                : {len(active)}")

    return active


# Bloque 5 — entry point
if __name__ == "__main__":
    aplicar_escenario("value_0")