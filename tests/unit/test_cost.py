from __future__ import annotations

from decimal import Decimal

from autoace.inference.cost import CostPolicy, PriceSnapshot


def test_cost_policy_allows_conservative_route_and_blocks_overage() -> None:
    policy = CostPolicy(
        PriceSnapshot("gemini-3.5-flash-lite", Decimal("0.15"), Decimal("1.25")),
        design_limit_per_minute=Decimal("0.0024"),
        hard_limit_per_minute=Decimal("0.003"),
    )
    allowed = policy.project(60, input_tokens=1920, output_tokens=320)
    assert allowed.hard_passes is True
    blocked = policy.project(5, input_tokens=340, output_tokens=1200)
    assert blocked.hard_passes is False


def test_cost_policy_uses_decimal_math() -> None:
    snapshot = PriceSnapshot("x", Decimal("0.15"), Decimal("1.25"))
    amount = snapshot.cost(input_tokens=1920, output_tokens=320)
    assert amount == Decimal("0.000688")
