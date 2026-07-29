r"""
agents/generator_base.py — common generator block (§5.4)
========================================================

Households, small-commercial entities and large generators share the same
formal structure: they **generate** waste (eq. 3) and allocate it across
four mutually exclusive destinations via a multinomial logit (revised
eq. 8): recyclables, organics, general/residual, and informal leakage
(waste that never enters the formal collection system).

Streams: $k\in\{R,O,G\}$ — recyclables, organics, general/residual, plus
the informal leakage share $\theta$.
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
    formal: float              # routed to the formal system (= generation - informal)
    informal: float            # routed to informal leakage (logit theta share)
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

    ``SCALE_DRIVER`` selects what generation scales with: households scale
    with served population ``N`` (default); small-commercial and large
    generators scale with the economic-activity index ``Y`` instead (design
    decision: household waste tracks population, but commercial/industrial
    waste tracks economic activity, not headcount) — see ``scale_value``.
    """

    SCALE_DRIVER = "N"  # overridden to "Y" by SmallCommercial, LargeGenerators

    def __init__(self, g: str, p: dict):
        self.g = g
        self.p = p
        self.gbar = p[f"gbar_{g}"]
        self.rho_min = p[f"rho_min_{g}"]


# Bloque 4 — generation method
    def scale_value(self, N: float, Y: float, N_ref: float) -> float:
        r"""Pick the generation-scale driver for this generator type.

        Households: raw served population $N_t$. Small-commercial / large
        generators: economic-activity index $Y_t$ (normalized, 1.0 in the
        base year) times the base-year population $N_{ref}$ — this keeps
        ``gbar_SC``/``gbar_LG`` in the same tons-per-capita-equivalent units
        as before, while letting economic growth (not population growth)
        drive commercial/industrial generation.
        """
        return N if self.SCALE_DRIVER == "N" else Y * N_ref

    def generation(self, A: float, scale: float) -> float:
        r"""Total generation $Q_g = \rho_g(A)\,\text{scale}\,\bar g_g$ — **eq. (3)**.

        Aggregate generation scales with the type-specific driver (population
        $N$ for households, economic index $Y$ for SC/LG — see
        ``scale_value``) and per-capita generation $\bar g_g$, scaled down by
        the education-driven reduction factor $\rho_g(A)\in[\rho_{\min},1]$.
        """
        return forms.rho(A, self.rho_min, self.p["kappa_rho"]) * scale * self.gbar


# Bloque 5 — allocate method
    def allocate(self, A: float, Psi: float, N: float, Y: float, N_ref: float,
                 pG: float, pR: float, pO: float) -> GeneratorOutput:
        r"""Route generation across R/O/G/informal via the multinomial logit.

        1. **Generation-scale driver.** $N$ for households, $Y\cdot N_{ref}$
           for SC/LG (``scale_value``) — see the ``Generator`` class docstring.
        2. **Four-way logit split (revised eq. 8).** $s_R,s_O,s_G,s_\theta$
           from $A,\Psi$ and the price wedge (``forms.sorting_shares``),
           summing to 1 by construction.
        3. **Stream quantities (eq. 6).** $Q_g^{k}=s_k\,Q_g,\;\;
           k\in\{R,O,G\}$; informal leakage $Q_g^{I}=s_\theta\,Q_g$.
        4. **Formal total.** $Q_g^{formal} = Q_g - Q_g^{I}
           = Q_g\,(s_R+s_O+s_G)$.
        """
        scale = self.scale_value(N, Y, N_ref)
        Qg = self.generation(A, scale)
        sR, sO, sG, sTheta = forms.sorting_shares(A, Psi, pG, pR, pO, self.p)
        informal = sTheta * Qg
        formal = Qg - informal
        return GeneratorOutput(
            generation=Qg, formal=formal, informal=informal,
            QR=sR * Qg, QO=sO * Qg, QG=sG * Qg,
            sR=sR, sO=sO, sG=sG)


# Bloque 6 — collection_payment method
    def collection_payment(self, out: GeneratorOutput,
                           pR: float, pO: float, pG: float) -> float:
        r"""Collection payment to MUN — **eq. (9)**.

        $$ R^{g\to MUN} = p_R Q_g^{R} + p_O Q_g^{O} + p_G Q_g^{G},
           \qquad p_G > p_R,\,p_O. $$
        """
        return pR * out.QR + pO * out.QO + pG * out.QG