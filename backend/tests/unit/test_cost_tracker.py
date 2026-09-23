"""Unit tests for the cost tracker."""

import pytest

from app.core.cost_tracker import CostTracker, LatencyTimer


def test_rejects_negative_prices():
    with pytest.raises(ValueError):
        CostTracker(-1.0, 0.0)


def test_estimate_usd():
    tracker = CostTracker(price_per_1k_input_tokens=0.003, price_per_1k_output_tokens=0.015)
    # 1000 in, 1000 out -> 0.003 + 0.015
    assert tracker.estimate_usd(1000, 1000) == pytest.approx(0.018)


def test_record_accumulates():
    tracker = CostTracker(0.003, 0.015)
    tracker.record("a", 1000, 0, 100.0)
    tracker.record("b", 0, 1000, 50.0)
    s = tracker.summary
    assert s.num_calls == 2
    assert s.total_input_tokens == 1000
    assert s.total_output_tokens == 1000
    assert s.total_tokens == 2000
    assert s.total_latency_ms == pytest.approx(150.0)
    assert s.total_usd_cost == pytest.approx(0.018)


def test_record_rejects_negative():
    tracker = CostTracker(0.003, 0.015)
    with pytest.raises(ValueError):
        tracker.record("x", -1, 0, 0.0)
    with pytest.raises(ValueError):
        tracker.record("x", 0, 0, -5.0)


def test_latency_timer():
    with LatencyTimer() as timer:
        pass
    assert timer.elapsed_ms >= 0.0
