# Bloque 1 — docstring
"""
xlsx_to_csv.py — Convert the Excel workbook to clean CSVs for the model.

Standalone:  python wm/xlsx_to_csv.py
From run.py: imported and called automatically before simulation.

Reads:  data/model_inputs.xlsx  (sheets: params_scalar, timeseries_exog, air_pollutant_factors)
Writes: data/params_scalar.csv, data/timeseries_exog.csv, data/air_pollutant_factors.csv

If the xlsx file does not exist, the step is skipped silently (the model
will use whatever CSVs are already in data/).
"""

# Bloque 2 — imports
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
XLSX     = DATA_DIR / "model_inputs.xlsx"

SHEETS = {
    "params_scalar":         "params_scalar.csv",
    "timeseries_exog":       "timeseries_exog.csv",
    "air_pollutant_factors": "air_pollutant_factors.csv",
}


# Bloque 3 — xlsx_to_csv function
def xlsx_to_csv(xlsx_path: Path | str = XLSX) -> None:
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        print(f"[xlsx_to_csv] No xlsx found at {xlsx_path} — skipping, using existing CSVs.")
        return

    print(f"[xlsx_to_csv] Converting {xlsx_path.name} → CSVs ...")
    for sheet_name, csv_name in SHEETS.items():
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
        out = DATA_DIR / csv_name
        df.to_csv(out, index=False, sep=",", decimal=".", encoding="utf-8")
        print(f"  {sheet_name:30s} → {csv_name} ({len(df)} rows, {len(df.columns)} cols)")
    print("[xlsx_to_csv] Done.\n")


# Bloque 4 — entry point
if __name__ == "__main__":
    xlsx_to_csv()