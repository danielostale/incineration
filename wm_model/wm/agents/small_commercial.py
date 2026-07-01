r"""
agents/small_commercial.py — Small Commercial (SC), §5.1.1.2
============================================================

Small commercial entities behave structurally like households: generation
scales with served population via $\bar g_{SC}$ and is reduced by awareness
$\rho_{SC}(A_t)$ (eq. 3); they sort across streams $R,O,G$ (eq. 8). All
waste enters the formal system — there is no informal leakage channel.
They differ from households only in calibrated parameter values.
"""
# Bloque 1 — import
from .generator_base import Generator


# Bloque 2 — SmallCommercial class
class SmallCommercial(Generator):
    def __init__(self, p: dict):
        super().__init__("SC", p)