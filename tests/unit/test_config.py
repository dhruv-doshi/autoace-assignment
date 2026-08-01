import json
from pathlib import Path

import pytest

from autoace.config import RemoteConfig


def test_remote_config_is_explicit_and_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "approval.json"
    path.write_text(json.dumps({
        "approved": True,
        "project_id": "p",
        "endpoint": "e",
        "region": "r",
        "retention_policy": "keep",
        "deletion_required": True,
        "research_budget_usd": "1.00",
        "secrets_source": "environment-only",
    }))
    with pytest.raises(ValueError):
        RemoteConfig.from_json(path)
