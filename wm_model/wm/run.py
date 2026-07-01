# Bloque 1 — docstring del módulo
r"""
run.py — entry point
====================

    python -m wm.run
    python wm/run.py

Pipeline:
1. Converts data/model_inputs.xlsx → CSV input files
2. Applies the selected scenario column from params_scalar
3. Loads calibration from the active CSV inputs
4. Runs the Stage-0 recursion with closure checks
5. Writes outputs_endogenous.csv
6. Writes MSW_Model_Documentation.xlsx
7. Prints a short closure report

Scenario logic
--------------
The Excel sheet params_scalar should contain:

    name | value_0 | value_1 | value_2 | value_3 | note

The selected scenario column is converted into the standard model input:

    name | value | note

This means the model code continues to read params_scalar.csv normally.
Only the scenario selector decides which value column is active.
"""


# Bloque 2 — imports and path fix
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

    from wm.config import Calibration
    from wm.simulate import simulate
    from wm.excel_report import write_model_excel_report
    from wm.xlsx_to_csv import xlsx_to_csv
    from wm.escenario import aplicar_escenario, SCENARIO_DESCRIPTIONS
else:
    from .config import Calibration
    from .simulate import simulate
    from .excel_report import write_model_excel_report
    from .xlsx_to_csv import xlsx_to_csv
    from .escenario import aplicar_escenario, SCENARIO_DESCRIPTIONS

# Project root (wm_model/), regardless of the working directory the script
# is launched from (terminal, `-m`, or the VS Code Run button).
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Bloque 3 — main function
def main(
    scenario: str = "value_0",
    out_path: str | Path = PROJECT_DIR / "outputs_endogenous.csv",
    excel_path: str | Path = PROJECT_DIR / "MSW_Model_Documentation.xlsx",
):
    # 0. Convert Excel inputs → raw CSVs.
    # At this point params_scalar.csv may still contain value_0/value_1/etc.
    xlsx_to_csv()

    # 1. Apply selected scenario.
    # This rewrites params_scalar.csv into the active format:
    # name | value | note
    aplicar_escenario(scenario=scenario)

    # 2. Load calibration from active CSVs.
    cal = Calibration.load()

    # 3. Run Stage-0 recursion.
    df = simulate(cal)

    # 4. Attach scenario metadata to every output row.
    scenario_info = SCENARIO_DESCRIPTIONS.get(scenario, {})

    scenario_name = scenario_info.get("name", "Undocumented scenario")
    scenario_logic = scenario_info.get("logic", "No scenario logic documented.")
    scenario_mechanisms = scenario_info.get(
        "active_mechanisms",
        "No active mechanisms documented.",
    )

    df.insert(1, "scenario_id", scenario)
    df.insert(2, "scenario_name", scenario_name)
    df.insert(3, "scenario_logic", scenario_logic)
    df.insert(4, "scenario_mechanisms", scenario_mechanisms)

    # 5. Standard CSV output.
    df.to_csv(out_path, index=False)

    # 6. Human-readable Excel documentation workbook.
    write_model_excel_report(df=df, out_path=excel_path)

    # 7. Build dashboard by running dashboard.py as a separate script.
    # This is intentionally done through subprocess rather than importing
    # build_dashboard, to avoid stale imports or path confusion.
    dashboard_script = Path(__file__).resolve().parent / "dashboard.py"

    print("-" * 60)
    print("Building dashboard through dashboard.py")
    print(f"dashboard script: {dashboard_script}")
    print("-" * 60)

    subprocess.run(
        [sys.executable, str(dashboard_script)],
        check=True,
        cwd=PROJECT_DIR,
    )

    # 8. Closure report.
    b, e = df.iloc[0], df.iloc[-1]
    line = "=" * 60

    print(line)
    print("STAGE 0 — CLOSURE REPORT")
    print(line)
    print(f"active scenario      : {scenario} — {scenario_name}")
    print(f"periods              : {len(df)}  ({df.year.min()}-{df.year.max()})")
    print(
        f"max |mass residual|  : {df.mass_residual.abs().max():.3e} tons  "
        f"-> {'CLOSED' if df.mass_residual.abs().max() < 1e-3 else 'FAIL'}"
    )
    print("transfer balance     : CLOSED (asserted each period)")
    print("-" * 60)

    print(
        f"baseline {int(b.year)}:  generation {b.gen_total:,.0f} t | "
        f"Q_HAUL {b.Q_HAUL:,.0f} t | landfill {b.Q_LF:,.0f} t"
    )

    print(
        f"            recovered {b.Q_mat:,.0f} t | D_LF {b.D_LF:.1%} | "
        f"net GHG {b.GHG_net:,.0f} tCO2e | D_env ${b.D_env:,.0f}"
    )

    print(
        f"end {int(e.year)}:       D_LF {e.D_LF:.1%} | A {e.A:,.1f} | "
        f"Psi {e.Psi:,.1f} | S_LF {e.S_LF:,.0f} t | S_ENV {e.S_ENV:,.0f} t"
    )

    print(line)
    print(f"CSV output written to    : {out_path}")
    print(f"Excel workbook written to: {excel_path}")
    print("Dashboard built through  : dashboard.py")

    return df

# value_0 — Stage 0 core accounting
# Baseline accounting parametrization. Generation and sorting are fixed.
# The model only routes waste through treatment capacity and computes flows,
# costs, emissions, damages and mass closure.

# value_1 — Source-separation behaviour
# Generation remains fixed, but education, convenience and relative prices
# can shift waste between residual waste, recyclables and organics.
# This tests sorting policy effects without assuming waste prevention.

# value_2 — Mechanical separation extension
# Adds mechanical separation of part of the mixed residual waste stream.
# The model can recover additional recyclables and organics before WTE
# or landfill, while keeping total generation fixed.

# value_3 — Behavioural prevention extension
# Awareness can reduce total waste generation through rho(A), in addition
# to affecting sorting behaviour. This is not the baseline; it is a
# behavioural sensitivity requiring empirical calibration.


# Bloque 4 — entry point
if __name__ == "__main__":
    main(scenario="value_1")