r"""
agents/generator_base.py — common generator block (§5.4)
========================================================

Households, small-commercial entities and large generators share the same
formal structure: they **generate** waste (eq. 3) and **sort** their waste
across three streams (eq. 8). All generated waste enters the formal system —
there is no informal leakage channel in this version of the model.

Streams: $k\in\{R,O,G\}$ — recyclables, organics, general/residual.
"""
# Bloque 1 — imports
from __future__ import annotations
from dataclasses import dataclass
from .. import forms


# Bloque 2 — GeneratorOutput dataclass
@dataclass
class GeneratorOutput:
    """Per-period physical output of one generator type (tons/yr)."""
    generation: float          # total generated, Q_g            (eq. 3)
    formal: float              # routed to the formal system (= generation)
    informal: float            # always 0.0 — no leakage channel
    QR: float                  # formal recyclable stream        (eq. 6)
    QO: float                  # formal organic stream           (eq. 6)
    QG: float                  # formal general stream           (eq. 6)
    sR: float
    sO: float
    sG: float


# Bloque 3 — Generator class and __init__
class Generator:
    r"""A generator agent of type ``g`` $\in\{H, SC, LG\}$.

    Parameters are pulled from the calibration by name using the suffix
    ``_{g}`` (e.g. ``gbar_H``, ``rho_min_SC``). All waste is routed to
    the formal system; there is no leakage channel.

    ``driver_col`` names the exogenous timeseries column that scales this
    generator's output in eq. 3 — served population ``N`` for households,
    or an economic-activity index for commercial/institutional generators
    whose waste tonnage tracks business activity, not headcount.
    """

    def __init__(self, g: str, p: dict, driver_col: str = "N"):
        self.g = g
        self.p = p
        self.driver_col = driver_col
        self.gbar = p[f"gbar_{g}"]
        self.rho_min = p[f"rho_min_{g}"]


# Bloque 4 — generation method
    def generation(self, A: float, driver: float) -> float:
        r"""Total generation $Q_g = \rho_g(A)\,X_g\,\bar g_g$ — **eq. (3)**.

        Aggregate generation scales with the generator's driver series
        $X_g$ (population for households; economic activity for
        commercial/institutional generators) and per-unit generation
        intensity $\bar g_g$, scaled down by the education-driven
        reduction factor $\rho_g(A)\in[\rho_{\min},1]$.
        """
        return forms.rho(A, self.rho_min, self.p["kappa_rho"]) * driver * self.gbar


# Bloque 5 — allocate method
    def allocate(self, A: float, Psi: float, driver: float,
                 pG: float, pR: float, pO: float) -> GeneratorOutput:
        r"""Route all generation into formal streams — no informal leakage.

        1. **Full formal participation.** $\theta_g \equiv 1$ for all
           generator types: $Q_g^{formal} = Q_g$, $Q_g^{informal} = 0$.
        2. **Sorting shares (eq. 8, rev. §5.4.1).**
           $s_R,s_O$ from $A,\Psi$ and the price wedge; $s_G=1-s_R-s_O$.
        3. **Stream quantities (eq. 6).**
           $Q_g^{k}=s_k\,Q_g^{formal},\;\; k\in\{R,O,G\}.$
        """
        Qg = self.generation(A, driver)
        formal   = Qg
        informal = 0.0
        sR, sO, sG = forms.sorting_shares(A, Psi, pG, pR, pO, self.p)
        return GeneratorOutput(
            generation=Qg, formal=formal, informal=informal,
            QR=sR * formal, QO=sO * formal, QG=sG * formal,
            sR=sR, sO=sO, sG=sG)


# Bloque 6 — collection_payment method
    def collection_payment(self, out: GeneratorOutput,
                           pR: float, pO: float, pG: float) -> float:
        r"""Collection payment to MUN — **eq. (9)**.

        $$ R^{g\to MUN} = p_R Q_g^{R} + p_O Q_g^{O} + p_G Q_g^{G},
           \qquad p_G > p_R,\,p_O. $$
        """
        return pR * out.QR + pO * out.QO + pG * out.QG