"""Decimal-safe external inference cost controller."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class PriceSnapshot:
    model_id: str
    input_per_million: Decimal
    output_per_million: Decimal

    def cost(self, *, input_tokens: int, output_tokens: int) -> Decimal:
        return (
            Decimal(input_tokens) * self.input_per_million
            + Decimal(output_tokens) * self.output_per_million
        ) / Decimal(1_000_000)


@dataclass(frozen=True)
class CostProjection:
    audio_minutes: Decimal
    estimated_usd: Decimal
    design_limit_usd: Decimal
    hard_limit_usd: Decimal
    design_passes: bool
    hard_passes: bool


@dataclass(frozen=True)
class CostPolicy:
    price: PriceSnapshot
    design_limit_per_minute: Decimal = Decimal("0.0024")
    hard_limit_per_minute: Decimal = Decimal("0.003")

    def project(
        self, audio_seconds: int | float, *, input_tokens: int, output_tokens: int
    ) -> CostProjection:
        minutes = Decimal(str(audio_seconds)) / Decimal(60)
        estimated = self.price.cost(input_tokens=input_tokens, output_tokens=output_tokens)
        design = minutes * self.design_limit_per_minute
        hard = minutes * self.hard_limit_per_minute
        return CostProjection(
            minutes, estimated, design, hard, estimated <= design, estimated <= hard
        )

    def require_hard_compliance(self, projection: CostProjection) -> None:
        if not projection.hard_passes:
            raise RuntimeError("remote route blocked: projected cost exceeds hard ceiling")


def audio_input_tokens(audio_seconds: float) -> int:
    return int(round(audio_seconds * 32))


@dataclass
class ResearchBudget:
    limit_usd: Decimal
    spent_usd: Decimal = Decimal("0")

    def authorize(self, amount: Decimal) -> None:
        if amount < 0:
            raise ValueError("research spend cannot be negative")
        if self.spent_usd + amount > self.limit_usd:
            raise RuntimeError("paid experiment blocked: research budget exceeded")

    def record(self, amount: Decimal) -> None:
        self.authorize(amount)
        self.spent_usd += amount

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"limit_usd": str(self.limit_usd), "spent_usd": str(self.spent_usd)},
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
