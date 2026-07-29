r"""
agents/transfer_station.py — Transfer station (TS), §5.5.2
==========================================================

In the V1 / Stage-0 model the transfer station is a **pass-through** node: it
consolidates and reloads flows for line-haul but neither transforms mass nor
levies an internal tipping fee. Each delivered stream leaves exactly as it
arrived:
$$ Q^{TS,out}_k = Q^{HAUL}_k . $$

It is given its own module so a future revision (transfer cost, line-haul
emissions, capacity limits) has a natural home without touching the rest of
the system.
"""
from __future__ import annotations


class TransferStation:
    def __init__(self, p: dict):
        self.p = p

    def pass_through(self, QR: float, QO: float, QG: float):
        r"""Identity pass-through: returns $(Q_R, Q_O, Q_G)$ unchanged."""
        return QR, QO, QG
