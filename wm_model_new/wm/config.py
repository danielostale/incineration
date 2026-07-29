r"""
config.py — calibration loader
==============================

Loads the **inputs** of the model (parameters + exogenous series + pollutant
factors) from the three CSV files and exposes them through a single
``Calibration`` object. Nothing here is endogenous: every value loaded is
something the modeller supplies. The model *computes* the rest.

Input files (in ``data/``)
--------------------------
- ``params_scalar.csv``        time-invariant parameters
- ``timeseries_exog.csv``      annual exogenous drivers + policy/scenario inputs
- ``air_pollutant_factors.csv`` emission factors and marginal damages

The split between *exogenous* (here) and *endogenous* (computed in
``simulate.py``) is the central accounting discipline of the model.

CSV files may use either comma or semicolon as separator; the loader
detects the separator automatically from the first line of each file.
"""
# Bloque 1 — imports
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import io
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# Bloque 2 — CSV loader with auto-detected separator
def _read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file accepting either comma or semicolon as separator.

    Reads the first line to detect the delimiter, then parses the full
    file. Also strips the UTF-8 BOM if present (common when saving from
    Excel on Windows).
    """
    raw = Path(path).read_text(encoding="utf-8-sig")
    sep = ";" if ";" in raw.split("\n")[0] else ","
    return pd.read_csv(io.StringIO(raw), sep=sep)


# Bloque 3 — Calibration dataclass
@dataclass
class Calibration:
    """Container for all model inputs.

    Attributes
    ----------
    p : dict[str, float]
        Scalar parameters, keyed by name (``params_scalar.csv``).
    ts : pandas.DataFrame
        Annual exogenous series, one row per year (``timeseries_exog.csv``).
    ap : pandas.DataFrame
        Air-pollutant emission factors and marginal damages.
    """
    p: dict
    ts: pd.DataFrame
    ap: pd.DataFrame

    # Bloque 4 — classmethod load
    @classmethod
    def load(cls, data_dir: Path | str = DATA_DIR) -> "Calibration":
        data_dir = Path(data_dir)
        p = (_read_csv(data_dir / "params_scalar.csv")
             .set_index("name")["value"].to_dict())
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