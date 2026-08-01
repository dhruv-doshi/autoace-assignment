from decimal import Decimal
from pathlib import Path

import pytest

from autoace.inference.cost import CostPolicy, PriceSnapshot, audio_input_tokens
from autoace.inference.gemini_audio import (
    GeminiAudioObserver,
    RemoteApproval,
    RemoteApprovalRequired,
)


def test_remote_observer_requires_approval_before_provider_call(tmp_path: Path) -> None:
    observer = GeminiAudioObserver(
        RemoteApproval(approved=False, project_id=None, endpoint=None, region=None),
        CostPolicy(PriceSnapshot("planning", Decimal("1"), Decimal("1"))),
    )
    projection = observer.cost_policy.project(
        60, input_tokens=audio_input_tokens(60), output_tokens=1
    )
    with pytest.raises(RemoteApprovalRequired):
        observer.observe(tmp_path / "missing.wav", projection=projection, prompt_version="v1")
