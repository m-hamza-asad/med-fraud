from __future__ import annotations

import sqlite3
import sys

connection = sqlite3.connect(sys.argv[1])
try:
    assert connection.execute("pragma integrity_check").fetchone()[0] == "ok"
    if len(sys.argv) > 2 and sys.argv[2] == "schema":
        assert connection.execute("select count(*) from sqlite_master where type='table' and name='users'").fetchone()[0] == 1
finally:
    connection.close()

