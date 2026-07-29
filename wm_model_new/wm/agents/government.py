r"""
agents/government.py — Government / Regulator (GOV), §5.6.8
==========================================================

GOV sits on the system boundary and interacts through prices and levies. It
**levies the landfill tax**, administers **Extended Producer Responsibility
(EPR)** payments in scenarios, and owns the regulatory damage prices used to
monetise externalities — the social cost of carbon $SCC$ and the marginal
damages $D_p$ of local air pollutants. GOV itself transforms no mass; in the
physical accounts it appears only through the tax it collects and the damage
prices it sets (applied in ``environment.py``).
"""
from __future__ import annotations


class Government:
    def __init__(self, p: dict, ap):
        self.p = p
        self.ap = ap                       # pollutant factors + marginal damages

    # --- landfill tax ------------------------------------------------------
    def landfill_tax(self, Q_LF: float, row) -> float:
        r"""Landfill tax levied on final landfill demand, $t^{LF}_t\,Q^{LF}_t$.

        Paid by the treatment operator, received by GOV.
        """
        return row.tax_LF * Q_LF

    # --- regulatory damage prices (used by Environment) -------------------
    @property
    def scc(self) -> float:
        r"""Social cost of carbon $SCC$ ($/tCO$_2$e)."""
        return self.p["SCC"]
