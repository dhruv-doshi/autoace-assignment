"""Explicit runtime configuration for optional remote observation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RemoteConfig:
    approved: bool
    project_id: str | None
    endpoint: str | None
    region: str | None
    retention_policy: str
    deletion_required: bool
    research_budget_usd: str
    secrets_source: str

    @classmethod
    def from_json(cls, path: Path) -> RemoteConfig:
        payload = json.loads(path.read_text())
        required = {
            "approved", "project_id", "endpoint", "region", "retention_policy",
            "deletion_required", "research_budget_usd", "secrets_source",
        }
        missing = required.difference(payload)
        if missing:
            raise ValueError(f"remote approval config missing keys: {sorted(missing)}")
        if payload["approved"] and payload["retention_policy"] != "delete-after-processing":
            raise ValueError("approved remote routing requires delete-after-processing")
        return cls(**{key: payload[key] for key in required})
