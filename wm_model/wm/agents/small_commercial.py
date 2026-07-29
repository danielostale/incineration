r"""
agents/small_commercial.py — Small Commercial (SC), §5.1.1.2
============================================================

Small commercial entities behave structurally like households: generation
is reduced by awareness $\rho_{SC}(A_t)$ (eq. 3) and they sort across
streams $R,O,G$ (eq. 8). All waste enters the formal system — there is no
informal leakage channel. Unlike households, SC generation scales with the
exogenous economic-activity index $Y_t$ rather than served population —
commercial waste tracks business activity, not headcount.
"""
# Bloque 1 — import
from .generator_base import Generator


# Bloque 2 — SmallCommercial class
class SmallCommercial(Generator):
    def __init__(self, p: dict):
        super().__init__("SC", p, driver_col="Y")