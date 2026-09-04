r"""
agents/transfer_station.py — Transfer-station operations
=======================================================

V2 keeps transfer stations mass-conserving but gives them an explicit economic
and environmental role. A share of public and private collection is assumed to
pass through transfer facilities; the shares, costs and emissions are synthetic
placeholders pending facility/routing data from Miami-Dade and FDEP.
"""

# Bloque 1 — imports
from __future__ import annotations
from dataclasses import dataclass


# Bloque 2 — output dataclass
@dataclass
class TransferOutput:
    QR: float
    QO: float
    QG: float
    Q_transfer: float
    cost: float
    ghg: float
    energy_use: float


# Bloque 3 — TransferStation class
class TransferStation:
    def __init__(self, p: dict):
        self.p = p

    def pass_through(self, QR: float, QO: float, QG: float,
                     Q_public: float = 0.0, Q_private: float = 0.0) -> TransferOutput:
        """Return unchanged mass plus transfer-operation diagnostics."""
        q_transfer = (
            self.p["transfer_share_public"] * Q_public
            + self.p["transfer_share_private"] * Q_private
        )
        return TransferOutput(
            QR=QR,
            QO=QO,
            QG=QG,
            Q_transfer=q_transfer,
            cost=self.p["c_transfer"] * q_transfer,
            ghg=self.p["g_transfer"] * q_transfer,
            energy_use=self.p["e_use_transfer"] * q_transfer,
        )
