r"""
forms.py — behavioural closed forms (assumed)
=============================================

The model text (Section 5) pins down the **sign and monotonicity** of the
behavioural responses but not their algebraic form. This module collects the
*assumed* closed forms in one place so they are easy to inspect and replace.
Every parameter used here is read from ``params_scalar.csv``; the functional
shape lives here.

> **Reviewer-facing caveat.** These shapes are modelling choices, not results.
> They are the smallest forms consistent with the qualitative restrictions in
> the text. Any quantitative claim that depends on them must be shown to be
> robust to reasonable alternative shapes.

Forms implemented
-----------------
1. Generation-reduction factor $\rho_g(A)$            — eq. (3)
2. Source-separation shares $s_R,\,s_O$               — eq. (8), rev. §5.4.1

Note: the formal-participation function $\theta_g(p_G)$ (eq. 4) has been
removed. All generators route 100% of waste to the formal system.
"""
# Bloque 1 — imports
from __future__ import annotations
import numpy as np

# Saturation rate that maps an unbounded stock (A or Psi) into a bounded
# behavioural driver in [0, 1). Isolated here as the one "shape knob".
_STOCK_SAT = 0.03


# Bloque 2 — saturate helper
def saturate(stock: float) -> float:
    r"""Bounded transform of a cumulative stock into a $[0,1)$ driver.

    $$ \tilde{x} = \tanh(\kappa_{\text{sat}}\, x), \qquad \kappa_{\text{sat}} = 0.03 $$

    Used for both awareness $A$ and convenience $\Psi$ so that an ever-growing
    stock produces a *saturating* (not unbounded) effect on behaviour.
    """
    return float(np.tanh(_STOCK_SAT * stock))


# Bloque 3 — rho: generation-reduction factor
def rho(A: float, rho_min: float, kappa_rho: float) -> float:
    r"""Generation-reduction factor $\rho_g(A_t)$ — **eq. (3)**.

    Education lowers the *physical quantity* of waste a generator produces,
    down to an irreducible floor $\rho_{\min}$ that consumption makes
    unavoidable:

    $$ \rho_g(A) = \rho_{\min} + (1-\rho_{\min})\,e^{-\kappa_\rho A},
       \qquad \frac{\partial \rho_g}{\partial A} < 0,\;\;
       \rho_g \in [\rho_{\min}, 1]. $$

    At $A=0$, $\rho_g = 1$ (baseline maximum generation); as awareness grows,
    generation falls toward the floor but never below it.
    """
    return rho_min + (1.0 - rho_min) * np.exp(-kappa_rho * A)


# Bloque 4 — sorting_shares
def sorting_shares(A: float, Psi: float, pG: float, pR: float, pO: float,
                   p: dict) -> tuple[float, float, float]:
    r"""Source-separation shares $s_R,\,s_O,\,s_G$ — **eq. (8), revised §5.4.1**.

    Each generator allocates its formal waste across recyclable ($R$), organic
    ($O$) and general ($G$) streams. The sorted shares rise with three forces:
    the **awareness** stock $A$ (built by education $E^{MUN}$), the
    **convenience** stock $\Psi$ (physical accessibility of recycling
    infrastructure, built by $X^{MUN}$), and the **price wedge** between the
    general fee and the sorted-stream fee:

    $$
    s_R = \min\!\Big(\bar s_R,\;
        s_R^0 + a^A_R\,\tilde A + a^\Psi_R\,\tilde\Psi
              + a^w_R\,(p_G-p_R)^+\Big),
    $$
    $$
    s_O = \min\!\Big(\bar s_O,\;
        s_O^0 + a^A_O\,\tilde A + a^\Psi_O\,\tilde\Psi
              + a^w_O\,(p_G-p_O)^+\Big),
    $$
    $$ s_G = 1 - s_R - s_O, $$

    with $\tilde A=\tanh(\kappa_{\text{sat}}A)$,
    $\tilde\Psi=\tanh(\kappa_{\text{sat}}\Psi)$, all partials of $s_R,s_O$ in
    $A,\Psi$ and the wedge non-negative (eq. 8 monotonicity), and a floor on
    $s_G$ so the general stream never vanishes.

    Returns ``(s_R, s_O, s_G)``.
    """
    dA, dP = saturate(A), saturate(Psi)
    use_psi = p["use_convenience"]
    sR = (p["sR0"] + p["aA_R"] * dA + use_psi * p["aPsi_R"] * dP
          + p["aw_R"] * max(0.0, pG - pR))
    sO = (p["sO0"] + p["aA_O"] * dA + use_psi * p["aPsi_O"] * dP
          + p["aw_O"] * max(0.0, pG - pO))
    sR = min(max(sR, 0.0), p["sR_max"])
    sO = min(max(sO, 0.0), p["sO_max"])
    if sR + sO > 0.95:
        k = 0.95 / (sR + sO)
        sR, sO = sR * k, sO * k
    return sR, sO, 1.0 - sR - sO