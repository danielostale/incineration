r"""
agents/generator_base.py — common generator block (§5.4)
========================================================

V2 generator architecture distinguishes single-family households (H),
multifamily households (MF), small commercial (SC) and large generators (LG).
The common allocation form is retained, but each type can now have its own
scale share and sorting/leakage intercepts.
"""

# Bloque 1 — imports
from __future__ import annotations
from dataclasses import dataclass
from .. import forms


# Bloque 2 — GeneratorOutput dataclass
@dataclass
class GeneratorOutput:
    generation: float
    formal: float
    informal: float
    QR: float
    QO: float
    QG: float
    sR: float
    sO: float
    sG: float


# Bloque 3 — Generator class and __init__
class Generator:
    SCALE_DRIVER = "N"

    def __init__(self, g: str, p: dict):
        self.g = g
        self.p = p
        self.gbar = p[f"gbar_{g}"]
        self.rho_min = p[f"rho_min_{g}"]


# Bloque 4 — generation scale + generation method
    def scale_value(self, N: float, Y: float, N_ref: float) -> float:
        """Return type-specific generation scale.

        ``scale_share_<g>`` is optional and defaults to 1. V2 uses it to split
        the former aggregate household block into single-family and
        multifamily components without mechanically increasing total
        residential generation in the synthetic baseline.
        """
        base = N if self.SCALE_DRIVER == "N" else Y * N_ref
        share = self.p.get(f"scale_share_{self.g}", 1.0)
        return base * share

    def generation(self, A: float, scale: float) -> float:
        return forms.rho(A, self.rho_min, self.p["kappa_rho"]) * scale * self.gbar


# Bloque 5 — allocate method
    def allocate(self, A: float, Psi: float, N: float, Y: float, N_ref: float,
                 pG: float, pR: float, pO: float) -> GeneratorOutput:
        scale = self.scale_value(N, Y, N_ref)
        Qg = self.generation(A, scale)
        sR, sO, sG, sTheta = forms.sorting_shares(
            A, Psi, pG, pR, pO, self.p, g=self.g
        )
        informal = sTheta * Qg
        formal = Qg - informal
        return GeneratorOutput(
            generation=Qg,
            formal=formal,
            informal=informal,
            QR=sR * Qg,
            QO=sO * Qg,
            QG=sG * Qg,
            sR=sR,
            sO=sO,
            sG=sG,
        )


# Bloque 6 — collection payment method
    def collection_payment(self, out: GeneratorOutput,
                           pR: float, pO: float, pG: float) -> float:
        return pR * out.QR + pO * out.QO + pG * out.QG
