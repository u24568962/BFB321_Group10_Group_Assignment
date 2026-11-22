# Unit tests for supplychain queueing_theory, using the hand calculations in file.
import pytest

from supply_chain.queueing_theory import mm1_metrics, mmc_metrics, utilisation


def test_mm1_hand_calculation():
    # lambda = 2, mu = 3: L = 2, Lq = 1.333, W = 1, Wq = 0.667
    r = mm1_metrics(2, 3)
    assert r["L"] == pytest.approx(2)
    assert r["Lq"] == pytest.approx(1.333, abs=0.001)
    assert r["W"] == pytest.approx(1)
    assert r["Wq"] == pytest.approx(0.667, abs=0.001)

def test_mmc_hand_calculation():
    # lambda = 10, mu = 4, c = 3: P_wait = 0.702, Wq = 0.351, Lq = 3.511
    r = mmc_metrics(10, 4, 3)
    assert r["P_wait"] == pytest.approx(0.702, abs=0.001)
    assert r["Wq"] == pytest.approx(0.351, abs=0.001)
    assert r["Lq"] == pytest.approx(3.511, abs=0.001)

def test_unstable_system_raises():
    # rho = 3 / 3 = 1 -> the queue grows forever
    with pytest.raises(ValueError):
        mm1_metrics(3, 3)

def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        utilisation(1, 0)   # service rate must be > 0
