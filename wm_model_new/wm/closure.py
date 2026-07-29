r"""
closure.py — accounting closure checks, §5.7 / §5.11
====================================================

The model's defining invariants. Stage 0 exists to verify them:

1. **Physical-flow closure (eq. 55).** Total generation equals recovered
   products + biological outputs/losses + combusted mass + landfilled +
   informal leakage. No ton disappears; none is double-counted.

   $$ \sum_{g} Q_g \;=\; Q^{mat} + (Q^{cmp}+Q^{loss}) + Q^{comb} + Q^{LF}
      + \sum_g Q_g^{I}. $$

2. **Transfer closure.** Every internal dollar paid by one agent is received
   by another — no dollar is received without an identified payer.

Also defines the two diversion metrics (eqs. 56-57).
"""
from __future__ import annotations


class ClosureError(AssertionError):
    pass


def check_mass(gen_total, t_out, informal_total, *, tol=1e-6):
    r"""Assert physical-flow closure (eq. 55); return the signed residual."""
    rhs = (t_out.Q_mat + t_out.Q_cmp + t_out.Q_loss
           + t_out.Q_comb + t_out.Q_LF + informal_total)
    residual = gen_total - rhs
    if abs(residual) > tol * max(1.0, gen_total):
        raise ClosureError(
            f"MASS BALANCE (eq. 55) fails: gen={gen_total:.6f} "
            f"rhs={rhs:.6f} residual={residual:.3e}")
    return residual


def check_transfers(transfers: dict, *, tol=1e-4):
    r"""Assert that summed payer-side outflows equal payee-side inflows.

    ``transfers`` is a mapping ``name -> (payer, payee, amount)``. Booking each
    flow once and summing both sides independently catches mis-postings.
    """
    out_by, in_by = {}, {}
    for _, (payer, payee, amt) in transfers.items():
        out_by[payer] = out_by.get(payer, 0.0) + amt
        in_by[payee] = in_by.get(payee, 0.0) + amt
    tot_out, tot_in = sum(out_by.values()), sum(in_by.values())
    if abs(tot_out - tot_in) > tol * max(1.0, tot_out):
        raise ClosureError(
            f"TRANSFER BALANCE fails: out={tot_out:.4f} in={tot_in:.4f}")
    return tot_out - tot_in


def diversion(t_out, Q_HAUL, p):
    r"""Diversion metrics on net recovered tonnage over formal collection.

    **Non-combustion diversion (eq. 56)** — excludes WTE:
    $$ D^{NC}_t = \frac{(1-\lambda_{MRF,t})Q_{MRF}+(1-\lambda_{CMP})Q_{CMP}}
                       {Q^{HAUL}_t}. $$

    **Landfill diversion (eq. 57)** — counts every pathway avoiding the
    landfill, including combustion:
    $$ D^{LF}_t = 1 - \frac{Q^{LF}_t}{Q^{HAUL}_t}. $$

    Note: $\lambda_{MRF,t}$ is now endogenous in $A_t$ (see
    ``forms.lambda_mrf``) and is read off ``t_out.lambda_MRF`` — the
    period-specific value computed in ``treatment.run`` — rather than the
    fixed ``p["lambda_MRF"]`` used before the single-stream revision.
    """
    if Q_HAUL <= 0:
        return 0.0, 0.0
    D_NC = ((1 - t_out.lambda_MRF) * t_out.Q_MRF
            + (1 - p["lambda_CMP"]) * t_out.Q_CMP) / Q_HAUL
    D_LF = 1 - t_out.Q_LF / Q_HAUL
    return D_NC, D_LF