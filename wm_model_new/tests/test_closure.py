"""V2 closure regression test: model must run and conserve mass."""
from wm.config import Calibration
from wm.simulate import simulate


def test_mass_and_transfer_closure():
    df = simulate(Calibration.load())  # transfer closure asserted each period

    assert df.mass_residual.abs().max() < 1e-3
    assert (df.Q_HAUL >= 0).all()
    assert (df.Q_FORMAL_TOTAL >= df.Q_HAUL).all()
    assert (df.Q_LF >= 0).all()
    assert (df.Q_CND_disposal >= 0).all()
    assert (df.Q_private_mat >= 0).all()
    assert (df.Q_mulch >= 0).all()
    assert (df.Q_CND_mat >= 0).all()
    assert ((df.D_NC >= 0) & (df.D_NC <= 1)).all()
    assert ((df.D_LF >= 0) & (df.D_LF <= 1)).all()
