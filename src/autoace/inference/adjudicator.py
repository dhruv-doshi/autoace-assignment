"""Optional evidence-only stronger-model adjudicator."""

from __future__ import annotations

from typing import Any

from autoace.inference.gemini_audio import RemoteApprovalRequired


class TextAdjudicator:
    def __init__(self, *, approved: bool) -> None:
        self.approved = approved

    def adjudicate(self, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.approved:
            raise RemoteApprovalRequired("text adjudication approval is not configured")
        if not evidence:
            return []
        raise RuntimeError(
            "Gemini 3.6 text adapter is disabled until approved credentials "
            "are configured"
        )
