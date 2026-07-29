r"""
agents/haulers.py — Collection agents (HAUL), §5.5.1
====================================================

Haulers collect the three formal streams from generators and deliver them to
the transfer station / treatment operator. They receive the municipal contract
payment $p^{HAUL}Q^{HAUL}$ (residential streams) and pay tipping fees at the
treatment gate; the gate fee is a pass-through that exactly equals the
operator's tipping revenue (eq. 43). They bear a real haulage cost
$c_{coll}$ per ton.

**Physical aggregation (eqs. 13-14).** The formal collected tonnage is the sum
over generators of each stream:
$$ Q^{HAUL}_k = \sum_{g\in\mathcal G} Q_g^{k}, \quad k\in\{R,O,G\}, \qquad
   Q^{HAUL} = \sum_k Q^{HAUL}_k. $$
"""
from __future__ import annotations


class Haulers:
    def __init__(self, p: dict):
        self.p = p

    def collection_cost(self, Q_HAUL: float) -> float:
        r"""Real haulage cost $C^{coll}_t = c_{coll}\,Q^{HAUL}_t$ (§5.5.1)."""
        return self.p["c_coll"] * Q_HAUL
