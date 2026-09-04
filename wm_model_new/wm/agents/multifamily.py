r"""
agents/multifamily.py — Multifamily residential generator (MF)
================================================================

FDEP reports single-family and multifamily waste separately. V2 therefore
represents multifamily households as a distinct generator type rather than
folding them into small commercial. The initial parameterization is synthetic;
FDEP generator-type tonnage/participation data will replace it.
"""

# Bloque 1 — import
from .generator_base import Generator


# Bloque 2 — Multifamily class
class Multifamily(Generator):
    SCALE_DRIVER = "N"

    def __init__(self, p: dict):
        super().__init__("MF", p)
