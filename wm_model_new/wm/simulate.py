r"""
simulate.py — Stage-0 forward recursion
========================================

Ties the agents together into the deterministic year-by-year recursion that
**is** the Stage-0 model. The within-period ordering mirrors the physical
network of §5.1: generation → collection → transfer → treatment → disposal →
environment, with the monetary counterparts booked alongside and the
behavioural stocks ($A,\Psi,S^{LF},S^{ENV}$) advanced through their laws of
motion at the end of each period.

Generated waste is allocated across four destinations via the multinomial
logit in ``forms.sorting_shares`` (revised eq. 8): recyclable, organic,
general, and informal leakage — $Q_g^{informal}$ is no longer identically
zero. The MRF reject/contamination fraction $\lambda_{MRF,t}$ is likewise
endogenous in awareness $A_t$ (``forms.lambda_mrf``, revised eq. 32),
computed once per year and passed into ``treat.run``.

State carried across periods
----------------------------
- $A$      awareness            (eq. 10a, advanced by MUN from $E^{MUN}$)
- $\Psi$   convenience          (eq. 10b, advanced by MUN from $X^{MUN}$)
- $S^{LF}$ landfilled stock     (§5.6.5, advanced by Treatment)
- $S^{ENV}$ informal stock      (eq. 65, advanced by accumulated informal
                                 leakage — no longer identically zero)
"""
# Bloque 1 — imports
from __future__ import annotations
import pandas as pd

from .config import Calibration
from . import forms
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
    S_ENV = p["S_ENV0"]  # informal leakage restored — stock accumulates
    N_ref = cal.ts["N"].iloc[0]  # base-year population, scales SC/LG via Y


# Bloque 4 — main year loop: generation + participation + sorting
    records = []
    for year in cal.years:
        row = cal.row(year)

        # 1) GENERATION + SORTING (revised eq. 8) ---------------------------
        # Four-way logit split per generator: R, O, G, informal (theta).
        QR = QO = QG = 0.0
        gen_total    = 0.0
        informal_total = 0.0          # sum of theta-share leakage, all g
        gen_to_mun   = 0.0
        per_gen      = {}
        for gen in generators:
            o = gen.allocate(A, Psi, row.N, row.Y, N_ref, row.p_G, row.p_R, row.p_O)
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
        # 3) TREATMENT (revised eqs. 31-40) ---------------------------------
        # lambda_MRF is endogenous in A_t (single-stream contamination,
        # revised eq. 32) — computed here, once per year, and passed in.
        lambda_MRF = forms.lambda_mrf(A, p)
        t_out = treat.run(QR, QO, QG, row, lambda_MRF)


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
            year=int(year), A=A, Psi=Psi,
            sR=per_gen["H"].sR, sO=per_gen["H"].sO, sG=per_gen["H"].sG,
            gen_total=gen_total, informal=informal_total, Q_HAUL=Q_HAUL,
            gen_H=per_gen["H"].generation, gen_SC=per_gen["SC"].generation,
            gen_LG=per_gen["LG"].generation,
            Q_HAUL_R=QR, Q_HAUL_O=QO, Q_HAUL_G=QG,
            Q_MRF=t_out.Q_MRF, Q_CMP=t_out.Q_CMP, Q_WTE=t_out.Q_WTE,
            Q_LF=t_out.Q_LF, Q_mat=t_out.Q_mat, Q_cmp=t_out.Q_cmp,
            Q_comb=t_out.Q_comb, Q_ash=t_out.Q_ash, E_WTE=t_out.E_WTE,
            lambda_MRF=t_out.lambda_MRF,
            S_LF=S_LF, S_ENV=S_ENV,
            gen_to_mun=gen_to_mun, mun_to_haul=mun_to_haul, tipping=tipping,
            rev_mat=rev_mat, rev_E=rev_E, landfill_tax=landfill_tax,
            net_MUN=net_MUN, net_HAUL=net_HAUL, net_T=net_T,
            GHG_dir=ext.GHG_dir, GHG_net=ext.GHG_net, E_net=ext.E_net,
            D_climate=ext.D_climate, D_air=ext.D_air, D_water=ext.D_water,
            D_env=ext.D_env,
            D_NC=D_NC, D_LF=D_LF, mass_residual=mass_res))


# Bloque 12 — state updates and return
        # --- advance stocks -----------------------------------------------
        A = mun.awareness_next(A, row.E_edu)
        Psi = mun.convenience_next(Psi, row.X_MUN)
        S_LF = treat.landfill_stock_next(S_LF, t_out.Q_LF)
        S_ENV = env.informal_stock_next(S_ENV, informal_total)

    return pd.DataFrame(records)