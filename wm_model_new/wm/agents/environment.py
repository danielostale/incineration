r"""
agents/environment.py — Environment and V2 externality accounting
==================================================================

Environmental accounting remains physically separate from monetary damages.
V2 adds explicit GHG/energy terms for transfer operations, private recovered-
material processing, yard-waste mulching and C&D processing/disposal. Local-air
pollutant factors remain limited to WTE/LF until facility/permit data are loaded;
new-node local pollutant factors are therefore not silently invented.
"""

# Bloque 1 — imports and dataclass
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Externalities:
    GHG_dir: float
    B_env: float
    GHG_net: float
    D_climate: float
    D_air: float
    D_water: float
    D_env: float
    E_net: float


# Bloque 2 — Environment class
class Environment:
    def __init__(self, p: dict, ap):
        self.p = p
        self.ap = ap

    def informal_stock_next(self, S_ENV: float, informal_total: float) -> float:
        return S_ENV + informal_total


# Bloque 3 — emissions, avoided emissions and damages
    def assess(self, t_out, Q_HAUL: float, S_ENV: float,
               Q_transfer: float = 0.0) -> Externalities:
        p, o = self.p, t_out

        GHG_dir = (
            p["g_coll"] * Q_HAUL
            + p["g_sep"] * o.Q_sep
            + p["g_transfer"] * Q_transfer
            + p["g_MRF"] * o.Q_MRF
            + p["g_private_processing"] * o.Q_private_proc
            + p["g_CMP"] * o.Q_CMP
            + p["g_MULCH"] * o.Q_MULCH
            + p["g_CND_MRF"] * o.Q_CND_MRF
            + p["g_CND_disposal"] * o.Q_CND_disposal
            + p["g_WTE"] * o.Q_WTE
            + p["g_LF"] * o.Q_LF
        )

        E_net = (
            p["e_E"] * o.Q_WTE
            - p["e_use_MRF"] * o.Q_MRF
            - p["e_use_private_processing"] * o.Q_private_proc
            - p["e_use_CMP"] * o.Q_CMP
            - p["e_use_MULCH"] * o.Q_MULCH
            - p["e_use_WTE"] * o.Q_WTE
            - p["e_use_LF"] * o.Q_LF
            - p["e_use_transfer"] * Q_transfer
            - p["e_use_sep"] * o.Q_sep
        )

        B_env = (
            p["b_MRF"] * (o.Q_mat + o.Q_private_mat)
            + p["b_CMP"] * o.Q_cmp
            + p["b_MULCH"] * o.Q_mulch
            + p["b_CND"] * o.Q_CND_mat
            + p["g_grid"] * o.E_WTE
        )
        GHG_net = GHG_dir - B_env

        D_climate = p["SCC"] * GHG_net

        # Local-air damage remains permit-factor based for WTE/LF only. New
        # treatment-node pollutant factors are intentionally omitted until the
        # FDEP/Oculus/air-permit data are processed.
        D_air = 0.0
        for _, r in self.ap.iterrows():
            AP_p = r.a_WTE * o.Q_WTE + r.a_LF * o.Q_LF + r.a_sep * o.Q_sep
            D_air += r.D_p * AP_p

        # Existing Stage-0 placeholder; only regular landfill is charged here.
        D_water = p["MD_water"] * p["a_LF_water"] * o.Q_LF

        D_env = D_climate + D_air + D_water + p["d_ENV"] * S_ENV

        return Externalities(
            GHG_dir=GHG_dir,
            B_env=B_env,
            GHG_net=GHG_net,
            D_climate=D_climate,
            D_air=D_air,
            D_water=D_water,
            D_env=D_env,
            E_net=E_net,
        )
