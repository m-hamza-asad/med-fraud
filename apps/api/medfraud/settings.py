from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("MEDFRAUD_DATA_DIR", ROOT / "data" / "local"))
    reports_dir: Path = Path(os.getenv("MEDFRAUD_REPORTS_DIR", ROOT / "data" / "reports"))
    session_hours: int = 8
    max_upload_mb: int = 50

    @property
    def database_path(self) -> Path:
        return self.data_dir / "medfraud.sqlite3"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


settings = Settings()
