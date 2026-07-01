r"""
agents/large_generators.py — Large Generators (LG), §5.1.1.3
============================================================

Large generators (institutions, large commercial/industrial accounts) are
contractually bound to the formal system. All waste enters formal collection
($\theta_{LG}\equiv 1$, consistent with the no-leakage assumption applied
uniformly across all generator types in this version of the model).
Generation is reduced by awareness (eq. 3) and sorted across streams
(eq. 8). Like Small Commercial, LG generation scales with the exogenous
economic-activity index $Y_t$ rather than served population $N_t$ —
institutional/commercial tonnage tracks business and institutional
activity, not residential headcount. In the full model, large generators
contract directly with haulers at stream prices $\pi_k^{LG}$; in Stage-0
their formal tonnage enters the same downstream physical accounting as
other generators.
"""
# Bloque 1 — import
from .generator_base import Generator


# Bloque 2 — LargeGenerators class
class LargeGenerators(Generator):
    def __init__(self, p: dict):
        super().__init__("LG", p, driver_col="Y")