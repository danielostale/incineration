r"""
agents/municipality.py — Municipality / County authority (MUN), §5.5 / §5.4.1
=============================================================================

MUN consolidates the fee-setting, contracting, education and
infrastructure-support functions of the municipal tier and the County DSWM
into a single public accounting block.

**Policy vector** (revised §5.4.1):
$$ \Omega^{MUN} = \{\,p_R,\,p_O,\,p_G,\;p^{HAUL},\;E^{MUN},\;X^{MUN}\,\}, $$
where $p_R,p_O,p_G$ are stream collection fees ($p_G>p_R,p_O$), $p^{HAUL}$ the
hauler contract payment, $E^{MUN}$ education spending and $X^{MUN}$ recycling-
infrastructure spending. In Stage 0 every element of $\Omega^{MUN}$ is read
from the exogenous series; in later stages MUN chooses them.

**Two flow-to-stock channels (revised §5.4.1).** MUN's two behavioural
expenditures accumulate into two distinct stocks that drive generator
behaviour — the symmetric architecture that motivated the revision:

- education $E^{MUN}\;\longrightarrow\;$ awareness $A$  (eq. 10a)
- infrastructure $X^{MUN}\;\longrightarrow\;$ convenience $\Psi$  (eq. 10b)

Awareness raises *both* generation-reduction (eq. 3) and sorting (eq. 8);
convenience raises sorting (eq. 8). The stocks are held by the simulator and
advanced through the laws of motion below.
"""
from __future__ import annotations


class Municipality:
    def __init__(self, p: dict):
        self.p = p

    # --- eq. (10a): awareness law of motion -------------------------------
    def awareness_next(self, A: float, E_edu: float) -> float:
        r"""Awareness stock law of motion — **eq. (10a)**.

        $$ A_{t+1} = A_t + \gamma\, E^{MUN}_t. $$

        Awareness is cumulative and (in the baseline) does not depreciate:
        recycling knowledge and sorting habits, once established, persist. A
        decay term can be reintroduced in robustness checks.
        """
        return A + self.p["gamma"] * E_edu

    # --- eq. (10b): convenience law of motion -----------------------------
    def convenience_next(self, Psi: float, X_mun: float) -> float:
        r"""Convenience stock law of motion — **eq. (10b)**.

        $$ \Psi_{t+1} = \Psi_t + \delta\, X^{MUN}_t. $$

        Convenience captures the physical accessibility of recycling
        infrastructure (drop-off density, cart availability), built up by
        infrastructure spending $X^{MUN}$.
        """
        return Psi + self.p["delta_psi"] * X_mun

    # --- eq. (51): total municipal expenditure ----------------------------
    def total_expenditure(self, row, Q_HAUL: float) -> float:
        r"""Total municipal expenditure — **eq. (51)**.

        $$ C^{MUN}_t = p^{HAUL}_t\,Q^{HAUL}_t + E^{MUN}_t + X^{MUN}_t. $$

        The hauler contract payment scales with formal collected tonnage; the
        two behavioural expenditures are lump sums set by policy.
        """
        return row.p_HAUL * Q_HAUL + row.E_edu + row.X_MUN

    # --- contract payment to haulers (component of eq. 51) ----------------
    def hauler_payment(self, row, Q_HAUL: float) -> float:
        r"""Contract payment MUN $\to$ HAUL: $p^{HAUL}_t\,Q^{HAUL}_t$."""
        return row.p_HAUL * Q_HAUL
