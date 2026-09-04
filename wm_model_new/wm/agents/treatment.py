r"""
agents/treatment.py — V2 physical treatment network
===================================================

FDEP-informed V2 keeps one mass-accounting module but distinguishes the
physical pathways that matter for calibration and policy analysis:

- public single-stream MRF;
- integrated private recovered-material processing for LG recyclables;
- food-organics composting;
- yard-waste mulching;
- dedicated C&D processing/disposal;
- residual routing with an explicit direct-landfill share and WTE-eligible
  residual;
- WTE ash to landfill.

Crucially, MRF/CMP/mulching rejects now rejoin the WTE-eligible residual stream
before final landfill disposal, rather than being sent directly to landfill.
C&D rejects remain on the dedicated C&D disposal pathway.

All newly introduced numerical parameters are synthetic placeholders in
``data/v2_synthetic_params.csv`` pending the empirical FDEP/Oculus pipeline.
"""

# Bloque 1 — imports
from __future__ import annotations
from dataclasses import dataclass, asdict


# Bloque 2 — TreatmentOutput dataclass
@dataclass
class TreatmentOutput:
    # Legacy compatibility fields.
    Q_sep: float
    Q_bypass: float
    Q_aftersep: float

    # Throughput by node.
    Q_MRF: float
    Q_private_proc: float
    Q_CMP: float
    Q_MULCH: float
    Q_CND_MRF: float
    Q_WTE: float
    Q_LF: float
    Q_CND_disposal: float

    # Recovered products and losses.
    Q_mat: float
    Q_private_mat: float
    Q_cmp: float
    Q_mulch: float
    Q_CND_mat: float
    Q_loss: float
    Q_loss_CMP: float
    Q_loss_MULCH: float
    Q_comb: float
    Q_ash: float
    E_WTE: float

    # Rejects / process losses returned to residual or disposal.
    rej_MRF: float
    rej_private: float
    rej_CMP: float
    rej_MULCH: float
    rej_CND: float
    lambda_MRF: float

    # Available material and residual routing.
    R_avail: float
    O_avail: float
    O_food_avail: float
    O_yard_avail: float
    Q_Gavail: float
    Q_LF_direct: float
    Q_WTE_eligible: float

    # Capacity diagnostics.
    overflow_R: float
    overflow_O: float
    overflow_food: float
    overflow_yard: float
    overflow_CND: float
    cap_gap_MRF: float
    cap_gap_CMP: float
    cap_gap_MULCH: float
    cap_gap_CND: float
    util_MRF: float
    util_CMP: float
    util_MULCH: float
    util_CND: float

    def as_dict(self):
        return asdict(self)


# Bloque 3 — Treatment class and constructor
class Treatment:
    def __init__(self, p: dict):
        self.p = p


# Bloque 4 — run method
    def run(self, QR: float, QO: float, QG: float, row,
            lambda_MRF: float, *, QR_private: float = 0.0,
            Q_CND: float = 0.0) -> TreatmentOutput:
        """Route public/private MSW and dedicated C&D through the V2 network."""
        p = self.p

        # --- Public MRF ----------------------------------------------------
        R_avail = QR
        Q_MRF = min(R_avail, row.K_MRF)
        overflow_R = max(0.0, R_avail - row.K_MRF)
        Q_mat = (1.0 - lambda_MRF) * Q_MRF
        rej_MRF = lambda_MRF * Q_MRF
        cap_gap_MRF = max(0.0, row.K_MRF - R_avail)
        util_MRF = Q_MRF / row.K_MRF if row.K_MRF > 0 else 0.0

        # --- Private recovered-material operator --------------------------
        # LG source-separated recyclables may bypass the public MRF. The
        # operator is modelled as vertically integrated hauler/processor/
        # offtaker; process rejects rejoin residual treatment.
        Q_private_proc = QR_private
        lambda_private = p["lambda_private_operator"]
        Q_private_mat = (1.0 - lambda_private) * Q_private_proc
        rej_private = lambda_private * Q_private_proc

        # --- Organics split: food composting vs yard-waste mulching -------
        O_avail = QO
        yard_share = min(1.0, max(0.0, p["yard_share_organics"]))
        O_yard_avail = yard_share * O_avail
        O_food_avail = O_avail - O_yard_avail

        # Food -> composting.
        Q_CMP = min(O_food_avail, row.K_CMP)
        overflow_food = max(0.0, O_food_avail - row.K_CMP)
        Q_cmp = (1.0 - p["lambda_CMP"] - p["ell_CMP"]) * Q_CMP
        rej_CMP = p["lambda_CMP"] * Q_CMP
        Q_loss_CMP = p["ell_CMP"] * Q_CMP
        cap_gap_CMP = max(0.0, row.K_CMP - O_food_avail)
        util_CMP = Q_CMP / row.K_CMP if row.K_CMP > 0 else 0.0

        # Yard -> mulching / yard processing.
        K_MULCH = p["K_MULCH"]
        Q_MULCH = min(O_yard_avail, K_MULCH)
        overflow_yard = max(0.0, O_yard_avail - K_MULCH)
        Q_mulch = (1.0 - p["lambda_MULCH"] - p["ell_MULCH"]) * Q_MULCH
        rej_MULCH = p["lambda_MULCH"] * Q_MULCH
        Q_loss_MULCH = p["ell_MULCH"] * Q_MULCH
        cap_gap_MULCH = max(0.0, K_MULCH - O_yard_avail)
        util_MULCH = Q_MULCH / K_MULCH if K_MULCH > 0 else 0.0

        overflow_O = overflow_food + overflow_yard
        Q_loss = Q_loss_CMP + Q_loss_MULCH

        # --- Dedicated C&D path -------------------------------------------
        cnd_process_share = min(1.0, max(0.0, p["cnd_process_share"]))
        Q_CND_to_MRF = cnd_process_share * Q_CND
        Q_CND_direct = Q_CND - Q_CND_to_MRF
        K_CND = p["K_CND_MRF"]
        Q_CND_MRF = min(Q_CND_to_MRF, K_CND)
        overflow_CND = max(0.0, Q_CND_to_MRF - K_CND)
        rej_CND = p["lambda_CND_MRF"] * Q_CND_MRF
        Q_CND_mat = (1.0 - p["lambda_CND_MRF"]) * Q_CND_MRF
        Q_CND_disposal = Q_CND_direct + overflow_CND + rej_CND
        cap_gap_CND = max(0.0, K_CND - Q_CND_to_MRF)
        util_CND = Q_CND_MRF / K_CND if K_CND > 0 else 0.0

        # --- Residual aggregation -> direct LF + WTE ----------------------
        # MRF/CMP/mulching/private-processor rejects now enter residual before
        # WTE, per the revised routing rule. C&D stays separate.
        Q_Gavail = (
            QG
            + overflow_R + rej_MRF + rej_private
            + overflow_food + rej_CMP
            + overflow_yard + rej_MULCH
        )

        direct_share = min(1.0, max(0.0, p["direct_LF_share_residual"]))
        Q_LF_direct = direct_share * Q_Gavail
        Q_WTE_eligible = Q_Gavail - Q_LF_direct

        Q_WTE = min(Q_WTE_eligible, row.K_WTE)
        Q_ash = p["lambda_WTE"] * Q_WTE
        Q_comb = (1.0 - p["lambda_WTE"]) * Q_WTE
        E_WTE = p["e_E"] * Q_WTE

        Q_LF_unprocessed = Q_WTE_eligible - Q_WTE
        Q_LF = Q_LF_direct + Q_LF_unprocessed + Q_ash

        return TreatmentOutput(
            Q_sep=0.0,
            Q_bypass=0.0,
            Q_aftersep=0.0,
            Q_MRF=Q_MRF,
            Q_private_proc=Q_private_proc,
            Q_CMP=Q_CMP,
            Q_MULCH=Q_MULCH,
            Q_CND_MRF=Q_CND_MRF,
            Q_WTE=Q_WTE,
            Q_LF=Q_LF,
            Q_CND_disposal=Q_CND_disposal,
            Q_mat=Q_mat,
            Q_private_mat=Q_private_mat,
            Q_cmp=Q_cmp,
            Q_mulch=Q_mulch,
            Q_CND_mat=Q_CND_mat,
            Q_loss=Q_loss,
            Q_loss_CMP=Q_loss_CMP,
            Q_loss_MULCH=Q_loss_MULCH,
            Q_comb=Q_comb,
            Q_ash=Q_ash,
            E_WTE=E_WTE,
            rej_MRF=rej_MRF,
            rej_private=rej_private,
            rej_CMP=rej_CMP,
            rej_MULCH=rej_MULCH,
            rej_CND=rej_CND,
            lambda_MRF=lambda_MRF,
            R_avail=R_avail,
            O_avail=O_avail,
            O_food_avail=O_food_avail,
            O_yard_avail=O_yard_avail,
            Q_Gavail=Q_Gavail,
            Q_LF_direct=Q_LF_direct,
            Q_WTE_eligible=Q_WTE_eligible,
            overflow_R=overflow_R,
            overflow_O=overflow_O,
            overflow_food=overflow_food,
            overflow_yard=overflow_yard,
            overflow_CND=overflow_CND,
            cap_gap_MRF=cap_gap_MRF,
            cap_gap_CMP=cap_gap_CMP,
            cap_gap_MULCH=cap_gap_MULCH,
            cap_gap_CND=cap_gap_CND,
            util_MRF=util_MRF,
            util_CMP=util_CMP,
            util_MULCH=util_MULCH,
            util_CND=util_CND,
        )


# Bloque 5 — integrated/public treatment operating cost
    def operating_cost(self, o: TreatmentOutput) -> float:
        p = self.p
        return (
            p["c_sep"] * o.Q_sep
            + p["c_MRF"] * o.Q_MRF
            + p["c_CMP"] * o.Q_CMP
            + p["c_MULCH"] * o.Q_MULCH
            + p["c_WTE"] * o.Q_WTE
            + p["c_LF"] * o.Q_LF
        )


# Bloque 6 — private/C&D real operating costs
    def cnd_operating_cost(self, o: TreatmentOutput) -> float:
        p = self.p
        return p["c_CND_MRF"] * o.Q_CND_MRF + p["c_CND_disposal"] * o.Q_CND_disposal


# Bloque 7 — tipping revenue
    def tipping_revenue(self, o: TreatmentOutput, row) -> float:
        # Until a dedicated local mulching gate fee is observed, use the CMP
        # gate fee as the synthetic proxy for yard-organics handling.
        t_mulch = self.p.get("t_MULCH", row.t_CMP)
        return (
            row.t_MRF * o.Q_MRF
            + row.t_CMP * o.Q_CMP
            + t_mulch * o.Q_MULCH
            + row.t_WTE * o.Q_WTE
            + row.t_LF * o.Q_LF
        )


# Bloque 8 — product and energy revenue owned by integrated/public treatment
    def product_revenue(self, o: TreatmentOutput, row):
        return (
            row.p_mat * o.Q_mat,
            row.p_cmp * o.Q_cmp,
            self.p["p_MULCH"] * o.Q_mulch,
            row.p_E * o.E_WTE,
        )


# Bloque 9 — stocks
    def landfill_stock_next(self, S_LF: float, Q_LF: float) -> float:
        return (1.0 - self.p["delta_LF"]) * S_LF + Q_LF

    def cnd_stock_next(self, S_CND: float, Q_CND_disposal: float) -> float:
        return (1.0 - self.p["delta_CND"]) * S_CND + Q_CND_disposal
