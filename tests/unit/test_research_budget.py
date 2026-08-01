from decimal import Decimal
from pathlib import Path

import pytest

from autoace.inference.cost import ResearchBudget
from autoace.inference.privacy import RemoteFileLedger, redact_error


def test_research_budget_is_fail_closed_and_persistable(tmp_path: Path) -> None:
    budget = ResearchBudget(limit_usd=Decimal("1.00"))
    budget.record(Decimal("0.25"))
    with pytest.raises(RuntimeError):
        budget.record(Decimal("0.80"))
    target = tmp_path / "budget.json"
    budget.save(target)
    assert '"spent_usd": "0.25"' in target.read_text()


def test_privacy_helpers_redact_and_cleanup(tmp_path: Path) -> None:
    secret = tmp_path / "audio.wav"
    secret.write_bytes(b"x")
    message = f"api_key=abc123 failed at {secret}"
    redacted = redact_error(message)
    assert "abc123" not in redacted
    assert str(secret) not in redacted
    with RemoteFileLedger() as ledger:
        ledger.register(secret)
    assert not secret.exists()
