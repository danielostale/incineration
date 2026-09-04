r"""
closure.py — V2 accounting closure checks
=========================================

V2 mass closure includes public/private recovered materials, food compost,
yard-waste mulch, C&D recovery/disposal, combustion, regular landfill and
informal leakage. Regulatory recycling credit is reported separately from
physical diversion so Florida statutory accounting is never conflated with
mass-based system performance.
"""

# Bloque 1 — exception
from __future__ import annotations


class ClosureError(AssertionError):
    pass


# Bloque 2 — physical mass closure
def check_mass(gen_total, t_out, informal_total, *, tol=1e-6):
    rhs = (
        t_out.Q_mat
        + t_out.Q_private_mat
        + t_out.Q_cmp
        + t_out.Q_mulch
        + t_out.Q_CND_mat
        + t_out.Q_loss
        + t_out.Q_comb
        + t_out.Q_LF
        + t_out.Q_CND_disposal
        + informal_total
    )
    residual = gen_total - rhs
    if abs(residual) > tol * max(1.0, gen_total):
        raise ClosureError(
            f"MASS BALANCE fails: gen={gen_total:.6f} "
            f"rhs={rhs:.6f} residual={residual:.3e}"
        )
    return residual


# Bloque 3 — internal transfer closure
def check_transfers(transfers: dict, *, tol=1e-4):
    out_by, in_by = {}, {}
    for _, (payer, payee, amt) in transfers.items():
        out_by[payer] = out_by.get(payer, 0.0) + amt
        in_by[payee] = in_by.get(payee, 0.0) + amt
    tot_out, tot_in = sum(out_by.values()), sum(in_by.values())
    if abs(tot_out - tot_in) > tol * max(1.0, tot_out):
        raise ClosureError(
            f"TRANSFER BALANCE fails: out={tot_out:.4f} in={tot_in:.4f}"
        )
    return tot_out - tot_in


# Bloque 4 — physical diversion metrics
def diversion(t_out, Q_formal_total, p):
    """Return non-combustion and landfill diversion on all formal tonnage."""
    if Q_formal_total <= 0:
        return 0.0, 0.0

    recovered_nc = (
        t_out.Q_mat
        + t_out.Q_private_mat
        + t_out.Q_cmp
        + t_out.Q_mulch
        + t_out.Q_CND_mat
    )
    D_NC = recovered_nc / Q_formal_total
    D_LF = 1.0 - (t_out.Q_LF + t_out.Q_CND_disposal) / Q_formal_total
    return D_NC, D_LF


# Bloque 5 — Florida regulatory-credit proxy
def florida_credit_proxy(t_out, Q_formal_total, p):
    """Synthetic placeholder for Florida recycling-credit accounting.

    The weights are deliberately explicit and separate from physical diversion.
    ``fl_credit_WTE`` is zero until the actual FDEP renewable-energy credit
    formula is implemented from the annual-report methodology.
    """
    if Q_formal_total <= 0:
        return 0.0

    credit_tons = (
        p["fl_credit_MRF"] * (t_out.Q_mat + t_out.Q_private_mat)
        + p["fl_credit_organics"] * (t_out.Q_cmp + t_out.Q_mulch)
        + p["fl_credit_CND"] * t_out.Q_CND_mat
        + p["fl_credit_WTE"] * t_out.Q_WTE
    )
    return credit_tons / Q_formal_total
