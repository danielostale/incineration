r"""
agents/construction.py — Construction & demolition generator (CND)
=================================================================

C&D is represented as a dedicated, privately managed material stream rather
than a fourth curbside stream shared by all generators. Generation scales with
the economic-activity index Y and a synthetic intensity parameter until the
FDEP annual C&D series is processed and calibrated.
"""

# Bloque 1 — imports
from __future__ import annotations
from dataclasses import dataclass


# Bloque 2 — output dataclass
@dataclass
class ConstructionOutput:
    generation: float
    Q_CND: float


# Bloque 3 — Construction class
class Construction:
    def __init__(self, p: dict):
        self.p = p

    def generate(self, Y: float, N_ref: float) -> ConstructionOutput:
        Q = self.p["gbar_CND"] * Y * N_ref
        return ConstructionOutput(generation=Q, Q_CND=Q)
