r"""
config.py — calibration loader
==============================

Loads the **inputs** of the model (parameters + exogenous series + pollutant
factors) and exposes them through a single ``Calibration`` object. Nothing here
is endogenous: every value loaded is something the modeller supplies. The
model *computes* the rest.

Core input files (in ``data/``)
-------------------------------
- ``params_scalar.csv``        time-invariant V1/scenario parameters
- ``timeseries_exog.csv``      annual exogenous drivers + policy/scenario inputs
- ``air_pollutant_factors.csv`` emission factors and marginal damages

Optional V2 structural overlay
------------------------------
- ``v2_synthetic_params.csv``  temporary structural parameters introduced by
  the FDEP-informed V2 redesign (multifamily, private haulers, C&D, mulching,
  transfer operations, regulatory-credit proxy). These values are explicitly
  labelled SYNTHETIC/EXPERT_INFORMED in that file and are meant to be replaced
  by the empirical data pipeline now being built under ``data_V2``.

The V2 overlay is merged *after* ``params_scalar.csv``. If a name appears in
both files, the V2 value wins. This lets the architecture evolve without
forcing a binary Excel-workbook rewrite while the empirical database is under
construction.

CSV files may use either comma or semicolon as separator; the loader detects
the separator automatically from the first line of each file.
"""

# Bloque 1 — imports
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import io
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
V2_SYNTHETIC_PARAMS = "v2_synthetic_params.csv"


# Bloque 2 — CSV loader with auto-detected separator
def _read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file accepting either comma or semicolon as separator."""
    raw = Path(path).read_text(encoding="utf-8-sig")
    sep = ";" if ";" in raw.split("\n")[0] else ","
    return pd.read_csv(io.StringIO(raw), sep=sep)


# Bloque 2b — scalar-parameter loader with optional V2 overlay
def _load_scalar_parameters(data_dir: Path) -> dict:
    """Load active scalar parameters and overlay V2 structural placeholders.

    ``params_scalar.csv`` remains the authoritative scenario-selected V1 file.
    ``v2_synthetic_params.csv`` is optional. When present, only its ``name``
    and ``value`` columns are read; provenance/status columns are retained in
    the CSV for auditability but are not model inputs themselves.
    """
    base = (_read_csv(data_dir / "params_scalar.csv")
            .set_index("name")["value"].to_dict())

    v2_path = data_dir / V2_SYNTHETIC_PARAMS
    if v2_path.exists():
        v2 = _read_csv(v2_path)
        required = {"name", "value"}
        missing = required - set(v2.columns)
        if missing:
            raise ValueError(
                f"{V2_SYNTHETIC_PARAMS} is missing required columns: {sorted(missing)}"
            )
        overlay = v2.dropna(subset=["name"]).set_index("name")["value"].to_dict()
        base.update(overlay)

    return base


# Bloque 3 — Calibration dataclass
@dataclass
class Calibration:
    """Container for all model inputs."""
    p: dict
    ts: pd.DataFrame
    ap: pd.DataFrame

    # Bloque 4 — classmethod load
    @classmethod
    def load(cls, data_dir: Path | str = DATA_DIR) -> "Calibration":
        data_dir = Path(data_dir)
        p = _load_scalar_parameters(data_dir)
        ts = _read_csv(data_dir / "timeseries_exog.csv")
        ap = _read_csv(data_dir / "air_pollutant_factors.csv")
        return cls(p=p, ts=ts, ap=ap)

    # Bloque 5 — convenience accessors
    @property
    def years(self):
        return self.ts["year"].tolist()

    def row(self, year: int) -> pd.Series:
        """Exogenous inputs for a given calendar year."""
        return self.ts.loc[self.ts["year"] == year].iloc[0]
