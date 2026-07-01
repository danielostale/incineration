"""Closure regression test: the model must run and balance."""
from wm.config import Calibration
from wm.simulate import simulate


def test_mass_and_transfer_closure():
    df = simulate(Calibration.load())          # asserts transfers each period
    assert df.mass_residual.abs().max() < 1e-3  # eq. 55
    assert (df.Q_HAUL >= 0).all()
    assert (df.Q_LF >= 0).all()
    # WTE off in baseline
    assert (df.Q_WTE == 0).all()
