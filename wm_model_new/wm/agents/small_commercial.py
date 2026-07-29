r"""
agents/small_commercial.py — Small Commercial (SC), §5.1.1.2
============================================================

Small commercial entities differ structurally from households in one key
way: generation scales with the economic-activity index $Y$ (business
volume), not served population $N$ — a small commercial account's waste
output tracks how much business it does, not how many people live nearby
(see ``Generator.SCALE_DRIVER`` / ``scale_value``). They are reduced by
awareness $\rho_{SC}(A_t)$ (eq. 3) and allocate across $R,O,G,\theta$ via
the same multinomial logit (revised eq. 8), sharing the informal-leakage
intercept with households (§5.4.1 design choice — see
forms.sorting_shares).
"""
# Bloque 1 — import
from .generator_base import Generator


# Bloque 2 — SmallCommercial class
class SmallCommercial(Generator):
    SCALE_DRIVER = "Y"

    def __init__(self, p: dict):
        super().__init__("SC", p)