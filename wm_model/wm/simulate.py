r"""
simulate.py — Stage-0 forward recursion
========================================

Ties the agents together into the deterministic year-by-year recursion that
**is** the Stage-0 model. The within-period ordering mirrors the physical
network of §5.1: generation → collection → transfer → treatment → disposal →
environment, with the monetary counterparts booked alongside and the
behavioural stocks ($A,\Psi,S^{LF},S^{ENV}$) advanced through their laws of
motion at the end of each period.

All generated waste enters the formal system. There is no informal leakage
channel: $Q_g^{informal} = 0$ for all generator types $g$.

State carried across periods
----------------------------
- $A$      awareness            (eq. 10a, advanced by MUN from $E^{MUN}$)
- $\Psi$   convenience          (eq. 10b, advanced by MUN from $X^{MUN}$)
- $S^{LF}$ landfilled stock     (§5.6.5, advanced by Treatment)
- $S^{ENV}$ informal stock      (eq. 65, always zero — retained for
                                 structural completeness and future use)
"""
# Bloque 1 — imports
from __future__ import annotations
import pandas as pd

from .config import Calibration
from .agents.households import Households
from .agents.small_commercial import SmallCommercial
from .agents.large_generators import LargeGenerators
from .agents.municipality import Municipality
from .agents.haulers import Haulers
from .agents.transfer_station import TransferStation
from .agents.treatment import Treatment
from .agents.government import Government
from .agents.environment import Environment
from . import closure


# Bloque 2 — simulate function header + agent instantiation
def simulate(cal: Calibration) -> pd.DataFrame:
    p = cal.p

    # --- instantiate the agents -------------------------------------------
    generators = [Households(p), SmallCommercial(p), LargeGenerators(p)]
    mun      = Municipality(p)
    haul     = Haulers(p)
    ts_node  = TransferStation(p)
    treat    = Treatment(p)
    gov      = Government(p, cal.ap)
    env      = Environment(p, cal.ap)


# Bloque 3 — initial stocks
    # --- initial stocks ----------------------------------------------------
    A     = p["A0"]
    Psi   = p["Psi0"]
    S_LF  = p["S_LF0"]
    S_ENV = 0.0          # no informal leakage — stock is identically zero


# Bloque 4 — main year loop: generation + participation + sorting
    records = []
    for year in cal.years:
        row = cal.row(year)

        # 1) GENERATION + SORTING (eqs. 3, 6, 8) ---------------------------
        # All waste is formal; informal = 0 for every generator type.
        QR = QO = QG = 0.0
        gen_total    = 0.0
        informal_total = 0.0          # always 0.0 — retained for closure eq. 55
        gen_to_mun   = 0.0
        per_gen      = {}
        for gen in generators:
            o = gen.allocate(A, Psi, row.N, row.p_G, row.p_R, row.p_O)
            QR += o.QR; QO += o.QO; QG += o.QG
            gen_total    += o.generation
            informal_total += o.informal          # accumulates 0.0
            gen_to_mun   += gen.collection_payment(o, row.p_R, row.p_O, row.p_G)
            per_gen[gen.g] = o


# Bloque 5 — collection + transfer
        # 2) COLLECTION + TRANSFER (eqs. 13-14; §5.5.2) --------------------
        Q_HAUL = QR + QO + QG
        QR, QO, QG = ts_node.pass_through(QR, QO, QG)     # identity in V1


# Bloque 6 — treatment
        # 3) TREATMENT (eqs. 22-40) ----------------------------------------
        t_out = treat.run(QR, QO, QG, row)


# Bloque 7 — monetary flows
        # 4) MONETARY FLOWS (internal transfers) ---------------------------
        mun_to_haul  = mun.hauler_payment(row, Q_HAUL)
        tipping      = treat.tipping_revenue(t_out, row)
        landfill_tax = gov.landfill_tax(t_out.Q_LF, row)
        rev_mat, rev_cmp, rev_E = treat.product_revenue(t_out, row)

        transfers = {
            "gen->mun":  ("GEN",  "MUN",  gen_to_mun),
            "mun->haul": ("MUN",  "HAUL", mun_to_haul),
            "haul->T":   ("HAUL", "T",    tipping),
            "T->gov":    ("T",    "GOV",  landfill_tax),
        }


# Bloque 8 — externalities
        # 5) EXTERNALITIES (eqs. 65-73) ------------------------------------
        ext = env.assess(t_out, Q_HAUL, S_ENV)


# Bloque 9 — closure checks
        # 6) CLOSURE CHECKS (eqs. 55-57) -----------------------------------
        mass_res = closure.check_mass(gen_total, t_out, informal_total)
        closure.check_transfers(transfers)
        D_NC, D_LF = closure.diversion(t_out, Q_HAUL, p)


# Bloque 10 — agent net balances
        # --- agent net balances (revenue - cost), for inspection ----------
        C_coll   = haul.collection_cost(Q_HAUL)
        C_T_op   = treat.operating_cost(t_out)
        net_MUN  = gen_to_mun - mun_to_haul
        net_HAUL = mun_to_haul - tipping - C_coll
        net_T    = tipping + rev_mat + rev_cmp + rev_E - C_T_op - landfill_tax


# Bloque 11 — record
        # --- record -------------------------------------------------------
        records.append(dict(
            year=int(year),
            A=A,
            Psi=Psi,

            # Source-separation shares, currently reported for households.
            sR=per_gen["H"].sR,
            sO=per_gen["H"].sO,
            sG=per_gen["H"].sG,

            # Generation and collection.
            gen_total=gen_total,
            informal=informal_total,
            Q_HAUL=Q_HAUL,
            Q_HAUL_R=QR,
            Q_HAUL_O=QO,
            Q_HAUL_G=QG,

            # Installed treatment capacities.
            K_MRF=row.K_MRF,
            K_CMP=row.K_CMP,
            K_WTE=row.K_WTE,

            # Treatment-node throughput.
            Q_MRF=t_out.Q_MRF,
            Q_CMP=t_out.Q_CMP,
            Q_WTE=t_out.Q_WTE,
            Q_LF=t_out.Q_LF,

            # Recovered outputs, residuals, combustion, ash, and energy.
            Q_mat=t_out.Q_mat,
            Q_cmp=t_out.Q_cmp,
            Q_loss=t_out.Q_loss,
            Q_comb=t_out.Q_comb,
            Q_ash=t_out.Q_ash,
            E_WTE=t_out.E_WTE,
            rej_MRF=t_out.rej_MRF,
            rej_CMP=t_out.rej_CMP,

            # Treatment availability and capacity diagnostics.
            R_avail=t_out.R_avail,
            O_avail=t_out.O_avail,
            Q_Gavail=t_out.Q_Gavail,

            overflow_R=t_out.overflow_R,
            overflow_O=t_out.overflow_O,

            cap_gap_MRF=t_out.cap_gap_MRF,
            cap_gap_CMP=t_out.cap_gap_CMP,

            util_MRF=t_out.util_MRF,
            util_CMP=t_out.util_CMP,

            # Stocks.
            S_LF=S_LF,
            S_ENV=S_ENV,

            # Monetary flows.
            gen_to_mun=gen_to_mun,
            mun_to_haul=mun_to_haul,
            tipping=tipping,
            rev_mat=rev_mat,
            rev_cmp=rev_cmp,
            rev_E=rev_E,
            landfill_tax=landfill_tax,

            # Agent balances.
            net_MUN=net_MUN,
            net_HAUL=net_HAUL,
            net_T=net_T,

            # Environmental outputs.
            GHG_dir=ext.GHG_dir,
            B_env=ext.B_env,
            GHG_net=ext.GHG_net,
            D_climate=ext.D_climate,
            D_air=ext.D_air,
            D_env=ext.D_env,
            E_net=ext.E_net,

            # Closure and diversion.
            D_NC=D_NC,
            D_LF=D_LF,
            mass_residual=mass_res,
        ))


# Bloque 12 — state updates and return
        # --- advance stocks -----------------------------------------------
        A = mun.awareness_next(A, row.E_edu)
        Psi = mun.convenience_next(Psi, row.X_MUN)
        S_LF = treat.landfill_stock_next(S_LF, t_out.Q_LF)
        S_ENV = env.informal_stock_next(S_ENV, informal_total)

    return pd.DataFrame(records)