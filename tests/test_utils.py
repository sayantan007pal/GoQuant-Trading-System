import pytest

from utils.fee_model import calculate_fee, FEE_TIERS
from utils.latency_timer import LatencyTimer


def test_calculate_fee_taker_and_maker():
    price = 100.0
    quantity = 2.0
    # Test taker fee
    fee = calculate_fee(price, quantity, fee_tier='Tier 0', is_taker=True)
    expected_rate = FEE_TIERS['Tier 0']['taker']
    assert fee == pytest.approx(price * quantity * expected_rate)

    # Test maker fee
    fee = calculate_fee(price, quantity, fee_tier='Tier 0', is_taker=False)
    expected_rate = FEE_TIERS['Tier 0']['maker']
    assert fee == pytest.approx(price * quantity * expected_rate)


def test_calculate_fee_invalid_tier():
    with pytest.raises(ValueError):
        calculate_fee(100.0, 1.0, fee_tier='InvalidTier', is_taker=True)


def test_latency_timer_with_mock(monkeypatch):
    # Simulate time progression
    times = [100.0, 110.0]

    def fake_time():
        return times.pop(0)

    monkeypatch.setattr('utils.latency_timer.time.time', fake_time)

    timer = LatencyTimer()
    latency_ms = timer.tick()
    # (110 - 100) * 1000 = 10000 ms
    assert latency_ms == pytest.approx(10000.0)