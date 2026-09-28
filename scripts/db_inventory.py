from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/local/medfraud.sqlite3")
connection = sqlite3.connect(path)
try:
    tables = [
        row[0]
        for row in connection.execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
        )
    ]
    print(
        json.dumps(
            {
                "path": str(path),
                "integrity": connection.execute("pragma integrity_check").fetchone()[0],
                "tables": tables,
                "counts": {
                    table: connection.execute(f'select count(*) from "{table}"').fetchone()[0]
                    for table in tables
                },
            },
            indent=2,
        )
    )
finally:
    connection.close()

