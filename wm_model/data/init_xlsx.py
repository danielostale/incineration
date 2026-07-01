
init_xlsx.py — One-time script combine existing CSVs into model_inputs.xlsx

Usage  python datainit_xlsx.py

from pathlib import Path
import pandas as pd
import io

DATA_DIR = Path(__file__).resolve().parent

def _read_csv(path)
    raw = path.read_text(encoding=utf-8-sig)
    sep = ; if ; in raw.split(n)[0] else ,
    dec = , if sep == ; else .
    return pd.read_csv(io.StringIO(raw), sep=sep, decimal=dec)

SHEETS = {
    params_scalar         DATA_DIR  params_scalar.csv,
    timeseries_exog       DATA_DIR  timeseries_exog.csv,
    air_pollutant_factors DATA_DIR  air_pollutant_factors.csv,
}

out = DATA_DIR  model_inputs.xlsx

with pd.ExcelWriter(out, engine=openpyxl) as writer
    for sheet_name, csv_path in SHEETS.items()
        df = _read_csv(csv_path)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f  {csv_path.name30s} → sheet '{sheet_name}' ({len(df)} rows))

print(fnCreated {out})
print(Open it in Excel, verify the values, and from now on edit ONLY this file.)