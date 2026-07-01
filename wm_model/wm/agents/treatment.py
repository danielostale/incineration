r"""
agents/treatment.py — Integrated treatment operator (T), §5.6
=============================================================

The treatment operator receives the three delivered streams and operates five
physical nodes — **separation/pre-treatment**, **MRF**, **organics (CMP)**,
**WTE**, and **landfill (LF)** — defined by the *physical quality* of the
stream, not the identity of the generator. Mass is conserved at every node:
nothing disappears and nothing is double-counted (the invariant checked in
``closure.py`` against eq. 55).

Node map
--------
- **Separation** (eqs. 22-29): source-separated $R,O$ go straight to their
  nodes; mixed general waste either bypasses or is mechanically separated,
  recovering fractions $\eta_R,\eta_O$.
- **MRF** (eqs. 31-32): recovers marketable material $Q^{mat}$; reject fraction
  $\lambda_{MRF}$ goes to landfill.
- **CMP** (eqs. 33-34): marketable compost $Q^{cmp}$; reject $\lambda_{CMP}$ to
  landfill; biological loss $\ell_{CMP}$ (moisture + CO$_2$) leaves as mass loss.
- **WTE** (eqs. 35-38): combusts residual up to capacity $K_{WTE}$; ash fraction
  $\lambda_{WTE}$; electricity $E^{WTE}=e_E\,Q_{WTE}$.
- **LF** (eqs. 39-40): receives the residual not combusted plus all rejects and
  ash; accumulates the cumulative landfilled stock $S^{LF}$.

Capacity diagnostics
--------------------
The module also reports whether source-separated material is actually processed
or blocked by downstream capacity:

- R_avail / O_avail: material available for MRF / CMP
- overflow_R / overflow_O: material available but not processed because capacity binds
- cap_gap_MRF / cap_gap_CMP: unused capacity
- util_MRF / util_CMP: throughput divided by installed capacity

These diagnostics are not separate mechanisms. They are accounting variables
needed to interpret why source-separation behaviour may or may not translate
into recovered material.
"""

# Bloque 1 — imports
from __future__ import annotations

from dataclasses import dataclass, asdict


# Bloque 2 — TreatmentOutput dataclass
@dataclass
class TreatmentOutput:
    """Per-period physical, energy, and capacity-diagnostic outputs."""

    # Separation / pre-treatment.
    Q_sep: float
    Q_bypass: float
    Q_aftersep: float

    # Treatment-node throughput.
    Q_MRF: float
    Q_CMP: float
    Q_WTE: float
    Q_LF: float

    # Recovered outputs, losses, combustion, ash, and energy.
    Q_mat: float
    Q_cmp: float
    Q_loss: float
    Q_comb: float
    Q_ash: float
    E_WTE: float

    # Treatment residuals.
    rej_MRF: float
    rej_CMP: float

    # Material available before capacity constraints.
    R_avail: float
    O_avail: float
    Q_Gavail: float

    # Capacity diagnostics.
    overflow_R: float
    overflow_O: float
    cap_gap_MRF: float
    cap_gap_CMP: float
    util_MRF: float
    util_CMP: float

    def as_dict(self):
        return asdict(self)


# Bloque 3 — Treatment class and constructor
class Treatment:
    def __init__(self, p: dict):
        self.p = p


# Bloque 4 — run method
    def run(self, QR: float, QO: float, QG: float, row) -> TreatmentOutput:
        r"""Route the three delivered streams through all treatment nodes.

        Parameters
        ----------
        QR:
            Source-separated recyclable stream delivered by haulers.

        QO:
            Source-separated organic stream delivered by haulers.

        QG:
            General / mixed residual stream delivered by haulers.

        row:
            Period-specific exogenous inputs, including installed capacities
            K_MRF, K_CMP, and K_WTE.

        Returns
        -------
        TreatmentOutput
            Physical outputs, environmental-relevant quantities, and capacity
            diagnostics for the period.
        """
        p = self.p

        # --- separation / pre-treatment (eqs. 22-27) ----------------------
        # Source-separated R,O move directly. A policy/decision share
        # `sep_share` of mixed general waste is mechanically separated.
        Q_sep = p["sep_share"] * QG
        Q_bypass = QG - Q_sep

        # Separation recovers R,O at rates eta_R, eta_O. The remainder remains
        # residual after separation.
        Q_aftersep = (1 - p["eta_R"] - p["eta_O"]) * Q_sep
        R_avail = QR + p["eta_R"] * Q_sep
        O_avail = QO + p["eta_O"] * Q_sep

        # --- MRF (eqs. 31-32) ---------------------------------------------
        # Processed up to capacity; overflow O_R is rerouted to residual.
        Q_MRF = min(R_avail, row.K_MRF)
        O_R = R_avail - Q_MRF

        Q_mat = (1 - p["lambda_MRF"]) * Q_MRF
        rej_MRF = p["lambda_MRF"] * Q_MRF

        # MRF capacity diagnostics.
        overflow_R = max(0.0, R_avail - row.K_MRF)
        cap_gap_MRF = max(0.0, row.K_MRF - R_avail)
        util_MRF = Q_MRF / row.K_MRF if row.K_MRF > 0 else 0.0

        # --- organics / CMP (eqs. 33-34) ----------------------------------
        # Processed up to capacity; overflow O_O is rerouted to residual.
        Q_CMP = min(O_avail, row.K_CMP)
        O_O = O_avail - Q_CMP

        Q_cmp = (1 - p["lambda_CMP"] - p["ell_CMP"]) * Q_CMP
        rej_CMP = p["lambda_CMP"] * Q_CMP
        Q_loss = p["ell_CMP"] * Q_CMP

        # CMP capacity diagnostics.
        overflow_O = max(0.0, O_avail - row.K_CMP)
        cap_gap_CMP = max(0.0, row.K_CMP - O_avail)
        util_CMP = Q_CMP / row.K_CMP if row.K_CMP > 0 else 0.0

        # --- residual aggregation -> WTE (eqs. 35-38) ---------------------
        # Residual = bypassed mixed waste + after-sep residual + node overflows.
        Q_Gavail = Q_bypass + Q_aftersep + O_R + O_O

        Q_WTE = min(Q_Gavail, row.K_WTE)
        Q_ash = p["lambda_WTE"] * Q_WTE
        Q_comb = (1 - p["lambda_WTE"]) * Q_WTE
        E_WTE = p["e_E"] * Q_WTE

        # --- landfill demand (eqs. 39-40) ---------------------------------
        Q_LF_dir = Q_Gavail - Q_WTE
        Q_LF = Q_LF_dir + rej_MRF + rej_CMP + Q_ash

        return TreatmentOutput(
            Q_sep=Q_sep,
            Q_bypass=Q_bypass,
            Q_aftersep=Q_aftersep,

            Q_MRF=Q_MRF,
            Q_CMP=Q_CMP,
            Q_WTE=Q_WTE,
            Q_LF=Q_LF,

            Q_mat=Q_mat,
            Q_cmp=Q_cmp,
            Q_loss=Q_loss,
            Q_comb=Q_comb,
            Q_ash=Q_ash,
            E_WTE=E_WTE,

            rej_MRF=rej_MRF,
            rej_CMP=rej_CMP,

            R_avail=R_avail,
            O_avail=O_avail,
            Q_Gavail=Q_Gavail,

            overflow_R=overflow_R,
            overflow_O=overflow_O,
            cap_gap_MRF=cap_gap_MRF,
            cap_gap_CMP=cap_gap_CMP,
            util_MRF=util_MRF,
            util_CMP=util_CMP,
        )


# Bloque 5 — operating cost
    def operating_cost(self, o: TreatmentOutput) -> float:
        r"""Operator cost $C^{op}_T$ — separation + per-node O&M.

        $$ C^{op}_T = c_{sep}Q^{sep}
                    + c_{MRF}Q_{MRF}
                    + c_{CMP}Q_{CMP}
                    + c_{WTE}Q_{WTE}
                    + c_{LF}Q_{LF}. $$
        """
        p = self.p

        return (
            p["c_sep"] * o.Q_sep
            + p["c_MRF"] * o.Q_MRF
            + p["c_CMP"] * o.Q_CMP
            + p["c_WTE"] * o.Q_WTE
            + p["c_LF"] * o.Q_LF
        )


# Bloque 6 — tipping revenue
    def tipping_revenue(self, o: TreatmentOutput, row) -> float:
        r"""Gate tipping revenue, equal to haulers' tipping payment.

        $$ R^{tip}_T =
            t_{MRF}Q_{MRF}
          + t_{CMP}Q_{CMP}
          + t_{WTE}Q_{WTE}
          + t_{LF}Q_{LF}. $$
        """
        return (
            row.t_MRF * o.Q_MRF
            + row.t_CMP * o.Q_CMP
            + row.t_WTE * o.Q_WTE
            + row.t_LF * o.Q_LF
        )


# Bloque 7 — product and energy revenue
    def product_revenue(self, o: TreatmentOutput, row):
        r"""Boundary-market revenues: material, compost, electricity.

        $$ R^{mat}=p^{mat}Q^{mat},\quad
           R^{cmp}=p^{cmp}Q^{cmp},\quad
           R^{E}=p^{E}E^{WTE}. $$

        Returns
        -------
        tuple
            ``(R_mat, R_cmp, R_E)``
        """
        return (
            row.p_mat * o.Q_mat,
            row.p_cmp * o.Q_cmp,
            row.p_E * o.E_WTE,
        )


# Bloque 8 — landfill stock law of motion
    def landfill_stock_next(self, S_LF: float, Q_LF: float) -> float:
        r"""Cumulative landfilled stock.

        $$ S^{LF}_{t+1} = (1-\delta_{LF})S^{LF}_t + Q^{LF}_t. $$
        """
        return (1 - self.p["delta_LF"]) * S_LF + Q_LF