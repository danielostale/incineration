r"""
wm — Miami-Dade municipal solid-waste model (Section 5), Stage 0
================================================================

A modular, paper-readable implementation of the deterministic physical +
monetary accounting model. One module per agent; each method maps 1:1 to a
numbered equation. Reading the package top to bottom ≈ reading Section 5.

Layout
------
- ``config``    load inputs (the three CSVs) into a ``Calibration``
- ``forms``     assumed behavioural closed forms (ρ, θ, sorting) — swappable
- ``agents/``   one module per agent (generators, MUN, HAUL, TS, T, GOV, ENV)
- ``closure``   mass-balance (eq. 55) + transfer-balance checks
- ``simulate``  the year-by-year recursion + laws of motion
- ``run``       entry point: load → simulate → check → write outputs
"""
from .config import Calibration
from .simulate import simulate

__all__ = ["Calibration", "simulate"]
