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
2. Source-separation + informal-leakage shares
   $s_R,\,s_O,\,s_G,\,s_\theta$ — eq. (8), rev. §5.4.1 (multinomial logit)
3. MRF reject/contamination fraction $\lambda_{MRF}(A)$ — revised eq. 32

Revision note (informal leakage restored). The formal-participation
function $\theta_g(p_G)$ (eq. 4) was previously removed (all generators
routed 100% of waste to the formal system). It is reinstated here as a
fourth logit alternative ``theta``, sharing the same intercept and
awareness/convenience coefficients across generator types (a modelling
choice, not a data constraint — the per-type parameters `leakage_H`,
`leakage_SC`, `leakage_LG` remain in params_scalar.csv for a future
differentiated specification).
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


# Bloque 4 — sorting_shares (multinomial logit, incl. informal leakage)
def sorting_shares(A: float, Psi: float, pG: float, pR: float, pO: float,
                    p: dict) -> tuple[float, float, float, float]:
    r"""Source-separation and informal-leakage shares — **revised eq. (8)**.

    Four mutually exclusive destinations for a generator's total waste:
    recyclable ($R$), organic ($O$), informal leakage ($\theta$, waste that
    bypasses the formal system entirely), and general/residual ($G$, the
    reference category, $V_G\equiv 0$ — required for logit identification).
    Utility indices:

    $$ V_R = s_R^0 + a^A_R\,\tilde A + a^\Psi_R\,\tilde\Psi
                   + a^w_R\,(p_G-p_R)^+ $$
    $$ V_O = s_O^0 + a^A_O\,\tilde A + a^\Psi_O\,\tilde\Psi
                   + a^w_O\,(p_G-p_O)^+ $$
    $$ V_\theta = \ell_0 + \kappa_\theta\,(p_G-\bar p)^+
                        - a^A_\theta\,\tilde A - a^\Psi_\theta\,\tilde\Psi $$

    with $\tilde A=\tanh(\kappa_{\text{sat}}A)$,
    $\tilde\Psi=\tanh(\kappa_{\text{sat}}\Psi)$. Shares are the softmax over
    $\{R,O,\theta,G{=}0\}$:

    $$ s_k = \frac{e^{V_k}}{e^{V_R}+e^{V_O}+e^{V_\theta}+1},
       \quad k\in\{R,O,\theta\}, \qquad
       s_G = \frac{1}{e^{V_R}+e^{V_O}+e^{V_\theta}+1}. $$

    This guarantees $s_R+s_O+s_\theta+s_G=1$ and all four shares in
    $(0,1)$ for *any* parameter values — no clipping or renormalization
    is needed, unlike the previous linear-additive specification (which
    is retained implicitly: $V_R,V_O$ use the same intercepts/coefficients
    as before, now reinterpreted as log-odds relative to $G$).

    > **Calibration caveat.** `sR0`, `sO0`, `aA_R`, `aw_R`, ... are ported
    > unchanged from the pre-logit linear specification as placeholders.
    > In a logit they are log-odds coefficients, not marginal share
    > effects — do not read quantitative magnitudes off this version
    > without re-calibration (SMM/GMM).

    Returns ``(s_R, s_O, s_G, s_theta)``.
    """
    dA, dP = saturate(A), saturate(Psi)
    use_psi = p["use_convenience"]

    V_R = (p["sR0"] + p["aA_R"] * dA + use_psi * p["aPsi_R"] * dP
           + p["aw_R"] * max(0.0, pG - pR))
    V_O = (p["sO0"] + p["aA_O"] * dA + use_psi * p["aPsi_O"] * dP
           + p["aw_O"] * max(0.0, pG - pO))
    V_theta = (p["leakage_H"] + p["kappa_theta"] * max(0.0, pG - p["pbar"])
               - p["aA_theta"] * dA - use_psi * p["aPsi_theta"] * dP)

    e_R, e_O, e_T = np.exp(V_R), np.exp(V_O), np.exp(V_theta)
    Z = e_R + e_O + e_T + 1.0
    sR, sO, sTheta = e_R / Z, e_O / Z, e_T / Z
    sG = 1.0 / Z
    return sR, sO, sG, sTheta


# Bloque 5 — lambda_mrf: endogenous MRF reject/contamination fraction
def lambda_mrf(A: float, p: dict) -> float:
    r"""MRF reject fraction $\lambda_{MRF}(A_t)$ — **revised eq. (32)**.

    Single-stream recycling means everything a generator sorts as
    "recyclable" is mechanically re-separated at the MRF, not delivered
    clean. Contamination — and therefore the reject fraction — falls as
    awareness $A_t$ rises (better-informed households put less
    non-recyclable material in the recycling stream):

    $$ \lambda_{MRF}(A_t) = \lambda_{min}
         + (\lambda_{max}-\lambda_{min})\,e^{-b\,A_t}, \qquad
       \lambda_{MRF}\in(\lambda_{min},\lambda_{max}]. $$

    Bounded by construction for any $A_t\geq 0$ — no clipping needed.
    $\lambda_{min}$/$\lambda_{max}$ are anchored to dual-stream vs.
    single-stream contamination rates reported for comparable Florida
    MRFs (CAPACITY_STUDY_COMBINED_FINAL_REPORT_2.pdf, §8): roughly 9-10%
    for dual-stream, 24-30% for single-stream facilities. $b$ is a
    placeholder pending calibration.

    > **Structural note.** This replaces the previous mechanical-separation
    > channel that recovered $R,O$ out of the *general* stream (eqs. 22-30,
    > $\eta_R,\eta_O,c_{sep},\text{sep\_share}$) — a pathway that does not
    > exist in Miami-Dade's single-stream system and has been removed from
    > ``agents/treatment.py``. Those parameters remain in
    > ``params_scalar.csv`` as orphaned/inactive for now.
    """
    return p["lambda_min_MRF"] + (p["lambda_max_MRF"] - p["lambda_min_MRF"]) * np.exp(-p["b_lambda_MRF"] * A)