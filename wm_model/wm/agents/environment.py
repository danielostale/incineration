r"""
agents/environment.py — Environment (ENV) & externality conversion, §5.10
=========================================================================

The environment is a residual sink: it makes no payments but accumulates
physical stocks and absorbs emissions that generate external damages.
Environmental outcomes are tracked as **physical flows and stocks first**, and
converted into monetary damages **only** through explicit conversion factors,
so physical emissions and external costs are never mixed without a defined
price.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Externalities:
    GHG_dir: float; B_env: float; GHG_net: float
    D_climate: float; D_air: float; D_env: float
    E_net: float

    # Direct GHG emissions attributed to each source node (eq. 66 terms).
    # Sum equals GHG_dir; kept separate for per-agent attribution (Sankey).
    GHG_haul: float
    GHG_sep: float
    GHG_MRF: float
    GHG_CMP: float
    GHG_WTE: float
    GHG_LF: float

    # Avoided-emission credits attributed to each crediting node
    # (eq. 69 terms). Sum equals B_env.
    B_MRF: float
    B_CMP: float
    B_WTE: float


class Environment:
    def __init__(self, p: dict, ap):
        self.p = p
        self.ap = ap

    # --- eq. (65): informal waste stock -----------------------------------
    def informal_stock_next(self, S_ENV: float, informal_total: float) -> float:
        r"""Informal waste stock law of motion — **eq. (65)**.

        $$ S^{ENV}_{t+1} = S^{ENV}_t + \sum_{g\in\mathcal G} Q_g^{I}. $$
        """
        return S_ENV + informal_total

    # --- eqs. (66)-(73): emissions and monetised damages ------------------
    def assess(self, t_out, Q_HAUL: float, S_ENV: float) -> Externalities:
        r"""Emissions, avoided emissions, and monetised damages.

        **Direct GHG (eq. 66).**
        $$ GHG^{dir}_t = g_{coll}Q^{HAUL}_t + g_{sep}Q^{sep}_t
                       + \sum_{j\in\mathcal J} g_j Q_{j,t}. $$

        **Local air pollutants (eq. 67).** For each $p\in\{PM_{2.5},NO_x,SO_2,
        Hg,\text{dioxins}\}$:
        $$ AP_{p,t} = a_{p,WTE}Q_{WTE,t} + a_{p,LF}Q^{LF}_t + a_{p,sep}Q^{sep}_t. $$

        **Net energy (eq. 68).**
        $$ E^{net}_t = e_E Q_{WTE,t}
                     - \sum_j e^{use}_j Q_{j,t} - e^{use}_{sep}Q^{sep}_t. $$

        **Avoided emissions (eq. 69) and net GHG (eq. 70).**
        $$ B^{env}_t = b_{MRF}Q^{mat}_t + b_{CMP}Q^{cmp}_t + g_{grid}E^{WTE}_t,
           \qquad GHG^{net}_t = GHG^{dir}_t - B^{env}_t. $$

        **Monetised damages (eqs. 71-73).**
        $$ D^{climate}_t = SCC\cdot GHG^{net}_t,\quad
           D^{air}_t = \sum_p D_p\,AP_{p,t},$$
        $$ D^{env}_t = D^{climate}_t + D^{air}_t + d_{ENV}\,S^{ENV}_t. $$
        """
        p, o = self.p, t_out

        # Direct GHG emissions, one term per source node (eq. 66).
        GHG_haul = p["g_coll"] * Q_HAUL
        GHG_sep  = p["g_sep"] * o.Q_sep
        GHG_MRF  = p["g_MRF"] * o.Q_MRF
        GHG_CMP  = p["g_CMP"] * o.Q_CMP
        GHG_WTE  = p["g_WTE"] * o.Q_WTE
        GHG_LF   = p["g_LF"] * o.Q_LF
        GHG_dir = GHG_haul + GHG_sep + GHG_MRF + GHG_CMP + GHG_WTE + GHG_LF

        E_net = (p["e_E"] * o.Q_WTE                                       # eq. 68
                 - p["e_use_MRF"] * o.Q_MRF - p["e_use_CMP"] * o.Q_CMP
                 - p["e_use_WTE"] * o.Q_WTE - p["e_use_LF"] * o.Q_LF
                 - p["e_use_sep"] * o.Q_sep)

        # Avoided-emission credits, one term per crediting node (eq. 69).
        B_MRF = p["b_MRF"] * o.Q_mat
        B_CMP = p["b_CMP"] * o.Q_cmp
        B_WTE = p["g_grid"] * o.E_WTE
        B_env = B_MRF + B_CMP + B_WTE
        GHG_net = GHG_dir - B_env                                        # eq. 70

        D_climate = p["SCC"] * GHG_net                                   # eq. 71
        D_air = 0.0                                                       # eq. 72
        for _, r in self.ap.iterrows():
            AP_p = r.a_WTE * o.Q_WTE + r.a_LF * o.Q_LF + r.a_sep * o.Q_sep
            D_air += r.D_p * AP_p
        D_env = D_climate + D_air + p["d_ENV"] * S_ENV                   # eq. 73

        return Externalities(GHG_dir=GHG_dir, B_env=B_env, GHG_net=GHG_net,
                             D_climate=D_climate, D_air=D_air, D_env=D_env,
                             E_net=E_net,
                             GHG_haul=GHG_haul, GHG_sep=GHG_sep,
                             GHG_MRF=GHG_MRF, GHG_CMP=GHG_CMP,
                             GHG_WTE=GHG_WTE, GHG_LF=GHG_LF,
                             B_MRF=B_MRF, B_CMP=B_CMP, B_WTE=B_WTE)
