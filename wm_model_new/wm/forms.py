r"""
forms.py — behavioural closed forms (assumed)
=============================================

Behavioural closed forms used by the model. These are modelling choices, not
empirical results. V2 keeps the common functional form but allows generator-
specific intercept offsets and informal-leakage intercepts so single-family,
multifamily, small-commercial and large-generator behaviour can later be
calibrated separately with FDEP generator-type data.
"""

# Bloque 1 — imports
from __future__ import annotations
import numpy as np

_STOCK_SAT = 0.03


# Bloque 2 — saturate helper
def saturate(stock: float) -> float:
    return float(np.tanh(_STOCK_SAT * stock))


# Bloque 3 — rho: generation-reduction factor
def rho(A: float, rho_min: float, kappa_rho: float) -> float:
    return rho_min + (1.0 - rho_min) * np.exp(-kappa_rho * A)


# Bloque 4 — sorting_shares (multinomial logit, generator-specific V2 offsets)
def sorting_shares(A: float, Psi: float, pG: float, pR: float, pO: float,
                   p: dict, g: str = "H") -> tuple[float, float, float, float]:
    r"""Source-separation and informal-leakage shares.

    V2 preserves the common logit coefficients but adds type-specific offsets
    ``dV_R_<g>`` and ``dV_O_<g>`` plus a type-specific leakage intercept
    ``leakage_<g>``. All offsets are zero in the synthetic structural baseline,
    so the extension changes architecture without pretending that behavioural
    differences have already been estimated.
    """
    dA, dP = saturate(A), saturate(Psi)
    use_psi = p["use_convenience"]

    dvr = p.get(f"dV_R_{g}", 0.0)
    dvo = p.get(f"dV_O_{g}", 0.0)
    leak = p.get(f"leakage_{g}", p.get("leakage_H", -2.3))

    V_R = (p["sR0"] + dvr + p["aA_R"] * dA
           + use_psi * p["aPsi_R"] * dP
           + p["aw_R"] * max(0.0, pG - pR))
    V_O = (p["sO0"] + dvo + p["aA_O"] * dA
           + use_psi * p["aPsi_O"] * dP
           + p["aw_O"] * max(0.0, pG - pO))
    V_theta = (leak + p["kappa_theta"] * max(0.0, pG - p["pbar"])
               - p["aA_theta"] * dA
               - use_psi * p["aPsi_theta"] * dP)

    e_R, e_O, e_T = np.exp(V_R), np.exp(V_O), np.exp(V_theta)
    Z = e_R + e_O + e_T + 1.0
    sR, sO, sTheta = e_R / Z, e_O / Z, e_T / Z
    sG = 1.0 / Z
    return sR, sO, sG, sTheta


# Bloque 5 — lambda_mrf: endogenous MRF reject/contamination fraction
def lambda_mrf(A: float, p: dict) -> float:
    return (p["lambda_min_MRF"]
            + (p["lambda_max_MRF"] - p["lambda_min_MRF"])
            * np.exp(-p["b_lambda_MRF"] * A))
