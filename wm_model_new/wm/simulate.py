r"""
simulate.py — V2 forward recursion
==================================

The V2 recursion keeps the Stage-0 accounting discipline but incorporates the
structural changes motivated by FDEP/Miami-Dade discussions:

- single-family and multifamily residential generators are separate;
- large generators can use a vertically integrated private hauler/processor/
  offtaker;
- C&D is a dedicated privately managed stream;
- organics split into food composting and yard-waste mulching;
- MRF/CMP/mulching/private-process rejects rejoin residual before WTE;
- a share of residual may still go directly to landfill;
- transfer stations carry explicit cost/emissions diagnostics;
- physical diversion and Florida regulatory-credit proxy are distinct.

New numerical values are synthetic placeholders in ``v2_synthetic_params.csv``
and are designed to be replaced by the empirical FDEP data pipeline.
"""

# Bloque 1 — imports
from __future__ import annotations
import pandas as pd

from .config import Calibration
from . import forms
from .agents.households import Households
from .agents.multifamily import Multifamily
from .agents.small_commercial import SmallCommercial
from .agents.large_generators import LargeGenerators
from .agents.construction import Construction
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

    generators = [
        Households(p),
        Multifamily(p),
        SmallCommercial(p),
        LargeGenerators(p),
    ]
    construction = Construction(p)
    mun = Municipality(p)
    haul = Haulers(p)
    ts_node = TransferStation(p)
    treat = Treatment(p)
    gov = Government(p, cal.ap)
    env = Environment(p, cal.ap)


# Bloque 3 — initial stocks
    A = p["A0"]
    Psi = p["Psi0"]
    S_LF = p["S_LF0"]
    S_CND = p["S_CND0"]
    S_ENV = p["S_ENV0"]
    N_ref = cal.ts["N"].iloc[0]


# Bloque 4 — main year loop: generation + source allocation
    records = []
    for year in cal.years:
        row = cal.row(year)

        per_gen = {}
        gen_total_msw = 0.0
        informal_total = 0.0
        for gen in generators:
            o = gen.allocate(
                A, Psi, row.N, row.Y, N_ref,
                row.p_G, row.p_R, row.p_O,
            )
            per_gen[gen.g] = o
            gen_total_msw += o.generation
            informal_total += o.informal

        cnd_out = construction.generate(row.Y, N_ref)
        gen_total = gen_total_msw + cnd_out.generation


# Bloque 5 — public/private collection split
        lg = per_gen["LG"]
        private_lg_share = min(1.0, max(0.0, p["private_LG_collection_share"]))
        private_recycling_share = min(
            1.0, max(0.0, p["private_LG_recycling_share"])
        )

        # LG tonnes privately collected (all formal streams).
        Q_PRIVATE_LG = private_lg_share * lg.formal
        Q_PUBLIC_LG = lg.formal - Q_PRIVATE_LG

        # Of privately collected LG recyclables, this share bypasses the public
        # MRF and enters the integrated private recovered-material processor.
        QR_private_proc = (
            private_lg_share * private_recycling_share * lg.QR
        )

        # Physical R/O/G delivered to the integrated treatment network. Private
        # LG O/G still enter downstream treatment; only the designated private
        # recyclable fraction bypasses the public MRF.
        QR_all = sum(o.QR for o in per_gen.values())
        QO_all = sum(o.QO for o in per_gen.values())
        QG_all = sum(o.QG for o in per_gen.values())
        QR_system = QR_all - QR_private_proc

        Q_PUBLIC_HAUL = (
            per_gen["H"].formal
            + per_gen["MF"].formal
            + per_gen["SC"].formal
            + Q_PUBLIC_LG
        )
        Q_PRIVATE_HAUL_MSW = Q_PRIVATE_LG
        Q_PRIVATE_HAUL_CND = cnd_out.Q_CND
        Q_PRIVATE_HAUL = Q_PRIVATE_HAUL_MSW + Q_PRIVATE_HAUL_CND

        # Compatibility: Q_HAUL remains formal MSW R+O+G, excluding the new
        # dedicated C&D stream. Q_FORMAL_TOTAL is the all-stream denominator.
        Q_HAUL = QR_all + QO_all + QG_all
        Q_FORMAL_TOTAL = Q_HAUL + cnd_out.Q_CND


# Bloque 6 — transfer operations (mass-conserving, explicit cost/emissions)
        ts_out = ts_node.pass_through(
            QR_system, QO_all, QG_all,
            Q_public=Q_PUBLIC_HAUL,
            Q_private=Q_PRIVATE_HAUL_MSW,
        )
        QR_system, QO_system, QG_system = ts_out.QR, ts_out.QO, ts_out.QG

        ts_public_cost = p["c_transfer"] * p["transfer_share_public"] * Q_PUBLIC_HAUL
        ts_private_cost = p["c_transfer"] * p["transfer_share_private"] * Q_PRIVATE_HAUL_MSW


# Bloque 7 — treatment
        lambda_MRF = forms.lambda_mrf(A, p)
        t_out = treat.run(
            QR_system,
            QO_system,
            QG_system,
            row,
            lambda_MRF,
            QR_private=QR_private_proc,
            Q_CND=cnd_out.Q_CND,
        )


# Bloque 8 — monetary flows and ownership
        # Generator payments to MUN: H/MF/SC plus only the non-private LG share.
        gen_to_mun = 0.0
        for g in ("H", "MF", "SC"):
            gen_to_mun += generators[[x.g for x in generators].index(g)].collection_payment(
                per_gen[g], row.p_R, row.p_O, row.p_G
            )
        lg_public_payment = (
            (1.0 - private_lg_share)
            * generators[[x.g for x in generators].index("LG")].collection_payment(
                lg, row.p_R, row.p_O, row.p_G
            )
        )
        gen_to_mun += lg_public_payment

        mun_to_haul = mun.hauler_payment(row, Q_PUBLIC_HAUL)

        # Private generator payments.
        LG_to_private = p["p_private_LG"] * Q_PRIVATE_LG
        CND_to_private = p["p_CND_haul"] * cnd_out.Q_CND

        # Treatment tipping revenue is allocated between public and private
        # haulers according to downstream MSW tonnage after private material
        # recovery. This is a temporary accounting allocation, not an observed
        # contract rule.
        tipping = treat.tipping_revenue(t_out, row)
        private_downstream = max(
            0.0, Q_PRIVATE_LG - QR_private_proc + t_out.rej_private
        )
        public_downstream = Q_PUBLIC_HAUL
        downstream_total = public_downstream + private_downstream
        private_tip_share = (
            private_downstream / downstream_total if downstream_total > 0 else 0.0
        )
        tipping_private = private_tip_share * tipping
        tipping_public = tipping - tipping_private

        landfill_tax = gov.landfill_tax(t_out.Q_LF, row)

        # Boundary-market revenues.
        rev_mat, rev_cmp, rev_mulch, rev_E = treat.product_revenue(t_out, row)
        rev_private_mat = row.p_mat * t_out.Q_private_mat
        rev_CND = p["p_CND_mat"] * t_out.Q_CND_mat
        private_rebate = p["private_rebate_share"] * rev_private_mat

        transfers = {
            "gen->mun": ("GEN", "MUN", gen_to_mun),
            "mun->haul": ("MUN", "HAUL_PUBLIC", mun_to_haul),
            "haul_public->T": ("HAUL_PUBLIC", "T", tipping_public),
            "LG->private": ("LG", "PRIVATE", LG_to_private),
            "CND->private": ("CND_GEN", "PRIVATE", CND_to_private),
            "private->T": ("PRIVATE", "T", tipping_private),
            "private->LG_rebate": ("PRIVATE", "LG", private_rebate),
            "T->gov": ("T", "GOV", landfill_tax),
        }


# Bloque 9 — externalities and closure checks
        ext = env.assess(
            t_out,
            Q_FORMAL_TOTAL,
            S_ENV,
            Q_transfer=ts_out.Q_transfer,
        )

        mass_res = closure.check_mass(gen_total, t_out, informal_total)
        closure.check_transfers(transfers)
        D_NC, D_LF = closure.diversion(t_out, Q_FORMAL_TOTAL, p)
        D_FL_credit = closure.florida_credit_proxy(t_out, Q_FORMAL_TOTAL, p)


# Bloque 10 — agent net balances and real resource cost
        C_coll_public = haul.collection_cost(Q_PUBLIC_HAUL)
        C_coll_private = haul.private_collection_cost(Q_PRIVATE_HAUL)
        C_private_proc = haul.private_processing_cost(t_out.Q_private_proc)
        C_CND = treat.cnd_operating_cost(t_out)
        C_T_op = treat.operating_cost(t_out)

        net_MUN = gen_to_mun - mun_to_haul
        net_HAUL = (
            mun_to_haul - tipping_public - C_coll_public - ts_public_cost
        )
        net_PRIVATE = (
            LG_to_private + CND_to_private
            + rev_private_mat + rev_CND
            - tipping_private
            - C_coll_private - C_private_proc - C_CND - ts_private_cost
            - private_rebate
        )
        net_T = (
            tipping + rev_mat + rev_cmp + rev_mulch + rev_E
            - C_T_op - landfill_tax
        )

        real_system_cost = (
            C_coll_public + C_coll_private
            + ts_out.cost
            + C_private_proc + C_CND + C_T_op
        )


# Bloque 11 — record
        records.append(dict(
            year=int(year),
            A=A,
            Psi=Psi,
            sR=per_gen["H"].sR,
            sO=per_gen["H"].sO,
            sG=per_gen["H"].sG,
            sR_MF=per_gen["MF"].sR,
            sO_MF=per_gen["MF"].sO,
            sG_MF=per_gen["MF"].sG,
            gen_total=gen_total,
            gen_total_msw=gen_total_msw,
            informal=informal_total,
            gen_H=per_gen["H"].generation,
            gen_SF=per_gen["H"].generation,
            gen_MF=per_gen["MF"].generation,
            gen_SC=per_gen["SC"].generation,
            gen_LG=per_gen["LG"].generation,
            gen_CND=cnd_out.generation,
            Q_HAUL=Q_HAUL,
            Q_FORMAL_TOTAL=Q_FORMAL_TOTAL,
            Q_PUBLIC_HAUL=Q_PUBLIC_HAUL,
            Q_PRIVATE_HAUL=Q_PRIVATE_HAUL,
            Q_PRIVATE_HAUL_MSW=Q_PRIVATE_HAUL_MSW,
            Q_PRIVATE_HAUL_CND=Q_PRIVATE_HAUL_CND,
            Q_HAUL_R=QR_all,
            Q_HAUL_O=QO_all,
            Q_HAUL_G=QG_all,
            Q_PUBLIC_MRF_R=QR_system,
            Q_PRIVATE_REC_R=QR_private_proc,
            Q_transfer=ts_out.Q_transfer,
            Q_MRF=t_out.Q_MRF,
            Q_private_proc=t_out.Q_private_proc,
            Q_CMP=t_out.Q_CMP,
            Q_MULCH=t_out.Q_MULCH,
            Q_CND_MRF=t_out.Q_CND_MRF,
            Q_WTE=t_out.Q_WTE,
            Q_LF=t_out.Q_LF,
            Q_CND_disposal=t_out.Q_CND_disposal,
            Q_mat=t_out.Q_mat,
            Q_private_mat=t_out.Q_private_mat,
            Q_cmp=t_out.Q_cmp,
            Q_mulch=t_out.Q_mulch,
            Q_CND_mat=t_out.Q_CND_mat,
            Q_loss=t_out.Q_loss,
            Q_comb=t_out.Q_comb,
            Q_ash=t_out.Q_ash,
            E_WTE=t_out.E_WTE,
            lambda_MRF=t_out.lambda_MRF,
            rej_MRF=t_out.rej_MRF,
            rej_private=t_out.rej_private,
            rej_CMP=t_out.rej_CMP,
            rej_MULCH=t_out.rej_MULCH,
            S_LF=S_LF,
            S_CND=S_CND,
            S_ENV=S_ENV,
            gen_to_mun=gen_to_mun,
            mun_to_haul=mun_to_haul,
            LG_to_private=LG_to_private,
            CND_to_private=CND_to_private,
            tipping=tipping,
            tipping_public=tipping_public,
            tipping_private=tipping_private,
            rev_mat=rev_mat,
            rev_private_mat=rev_private_mat,
            rev_CND=rev_CND,
            rev_cmp=rev_cmp,
            rev_mulch=rev_mulch,
            rev_E=rev_E,
            private_rebate=private_rebate,
            landfill_tax=landfill_tax,
            net_MUN=net_MUN,
            net_HAUL=net_HAUL,
            net_PRIVATE=net_PRIVATE,
            net_T=net_T,
            real_system_cost=real_system_cost,
            GHG_dir=ext.GHG_dir,
            GHG_net=ext.GHG_net,
            E_net=ext.E_net,
            D_climate=ext.D_climate,
            D_air=ext.D_air,
            D_water=ext.D_water,
            D_env=ext.D_env,
            D_NC=D_NC,
            D_LF=D_LF,
            D_FL_credit_proxy=D_FL_credit,
            mass_residual=mass_res,
        ))


# Bloque 12 — state updates and return
        A = mun.awareness_next(A, row.E_edu)
        Psi = mun.convenience_next(Psi, row.X_MUN)
        S_LF = treat.landfill_stock_next(S_LF, t_out.Q_LF)
        S_CND = treat.cnd_stock_next(S_CND, t_out.Q_CND_disposal)
        S_ENV = env.informal_stock_next(S_ENV, informal_total)

    return pd.DataFrame(records)
