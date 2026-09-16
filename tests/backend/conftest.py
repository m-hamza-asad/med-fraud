from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEDFRAUD_DATA_DIR", str(tmp_path))

