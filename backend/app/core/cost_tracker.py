"""Per-request cost, token, and latency accounting.

Every hop that spends an LLM/retrieval call records its tokens and latency here.
Estimated USD cost uses *configurable* published per-token pricing constants (see
``config.py``) so nothing is hardcoded and pricing can be updated centrally.

The accumulated summary is attached to every API response so the frontend can
chart cost vs. quality across strategies — the core comparison the dissertation
makes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CallCost:
    """Cost record for a single LLM/retrieval call."""

    label: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    usd_cost: float


@dataclass
class CostSummary:
    """Aggregate cost/latency/token totals for a request."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_usd_cost: float = 0.0
    total_latency_ms: float = 0.0
    num_calls: int = 0
    calls: list[CallCost] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens


class CostTracker:
    """Accumulates cost across a single request's hops.

    Pricing is expressed per 1,000 tokens and injected from settings, so the same
    tracker works for any model by passing different constants.
    """

    def __init__(
        self,
        price_per_1k_input_tokens: float,
        price_per_1k_output_tokens: float,
    ) -> None:
        if price_per_1k_input_tokens < 0 or price_per_1k_output_tokens < 0:
            raise ValueError("prices must be non-negative")
        self.price_in = price_per_1k_input_tokens
        self.price_out = price_per_1k_output_tokens
        self._summary = CostSummary()

    def estimate_usd(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate USD cost for a call from its token counts."""
        return (
            (input_tokens / 1000.0) * self.price_in
            + (output_tokens / 1000.0) * self.price_out
        )

    def record(
        self,
        label: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
    ) -> CallCost:
        """Record one call and fold it into the running totals."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts must be non-negative")
        if latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        usd = self.estimate_usd(input_tokens, output_tokens)
        call = CallCost(
            label=label,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            usd_cost=usd,
        )
        s = self._summary
        s.total_input_tokens += input_tokens
        s.total_output_tokens += output_tokens
        s.total_usd_cost += usd
        s.total_latency_ms += latency_ms
        s.num_calls += 1
        s.calls.append(call)
        return call

    @property
    def summary(self) -> CostSummary:
        return self._summary


class LatencyTimer:
    """Context manager that measures wall-clock latency in milliseconds.

    Usage::

        with LatencyTimer() as t:
            do_work()
        elapsed_ms = t.elapsed_ms
    """

    def __init__(self) -> None:
        self._start = 0.0
        self.elapsed_ms = 0.0

    def __enter__(self) -> LatencyTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000.0
