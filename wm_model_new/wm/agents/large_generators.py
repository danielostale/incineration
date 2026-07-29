r"""
agents/large_generators.py — Large Generators (LG), §5.1.1.3
============================================================

Large generators (institutions, large commercial/industrial accounts) are
described in the model text as contractually bound to the formal system.
As of the informal-leakage revision (§5.4.1, revised eq. 8), the informal
share $\theta$ is shared across all three generator types by an explicit
modelling decision — LG therefore inherits a positive informal-leakage
share in the current calibration, which sits in tension with the
"contractually bound" characterization above. This is a known
inconsistency, not an oversight: differentiating $\theta$ by generator
type (`leakage_H`, `leakage_SC`, `leakage_LG` already exist in
params_scalar.csv) is the fix, deferred to a future revision. Generation
scales with the economic-activity index $Y$ (not served population $N$
— see ``Generator.SCALE_DRIVER`` / ``scale_value``: large-generator waste
output tracks economic/industrial activity, not headcount) and is reduced
by awareness (eq. 3). In the full model, large generators contract
directly with haulers at stream prices $\pi_k^{LG}$; in Stage-0 their
formal tonnage enters the same downstream physical accounting as other
generators.
"""
# Bloque 1 — import
from .generator_base import Generator


# Bloque 2 — LargeGenerators class
class LargeGenerators(Generator):
    SCALE_DRIVER = "Y"

    def __init__(self, p: dict):
        super().__init__("LG", p)