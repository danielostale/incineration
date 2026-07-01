r"""
agents/households.py — Households (H), §5.1.1.1
===============================================

**Physical role.** Households are the primary heterogeneous generators of
municipal solid waste. Aggregate household generation scales with served
population $N_t$ and average per-capita generation $\bar g_H$, scaled by the
education-driven reduction factor $\rho_H(A_t)$ (eq. 3). All household waste
enters the formal collection system — there is no informal leakage channel.
Households sort their formal waste across streams $R,O,G$ (eq. 8).

**Monetary role.** Households pay stream-differentiated fees to MUN, with
$p_G>p_R,p_O$ creating the financial incentive to sort (eq. 9).
"""
# Bloque 1 — import
from .generator_base import Generator


# Bloque 2 — Households class
class Households(Generator):
    def __init__(self, p: dict):
        super().__init__("H", p)