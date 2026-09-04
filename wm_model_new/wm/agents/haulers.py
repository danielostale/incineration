r"""
agents/haulers.py — Public and private collection agents
========================================================

V2 distinguishes the municipal/public collection system from private haulage
used by large generators and C&D. Physical ownership is kept separate from the
waste-treatment physics: the simulator can allocate tipping payments and
private recovered-material revenue without pretending all formal tons are
handled by one hauler.
"""

# Bloque 1 — imports
from __future__ import annotations


# Bloque 2 — Haulers class
class Haulers:
    def __init__(self, p: dict):
        self.p = p

    def collection_cost(self, Q_public: float) -> float:
        """Real public/municipal haulage cost."""
        return self.p["c_coll"] * Q_public

    def private_collection_cost(self, Q_private: float) -> float:
        """Real private haulage cost for LG and C&D streams."""
        return self.p["c_private_coll"] * Q_private

    def private_processing_cost(self, Q_private_recycling: float) -> float:
        """Real processing cost at the integrated private recovered-material node."""
        return self.p["c_private_processing"] * Q_private_recycling
