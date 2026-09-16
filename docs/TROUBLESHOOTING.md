# Troubleshooting

- **Python missing:** setup checks system Python, then the Codex bundled 3.12 runtime. Install compatible Python if neither exists.
- **Dependency download interrupted:** rerun `scripts/setup.ps1`; installation is idempotent.
- **Port occupied:** start increments API and web ports and prints the chosen URL. It never terminates unrelated processes.
- **Database problem:** preserve `data/local/medfraud.sqlite3`; run backup before repair. Startup health reports registry/database state.
- **Invalid import:** correct exact issue rows and retry; a blocking batch writes no claims.
- **Duplicate import:** the checksum returns the prior batch; canonical rows are not duplicated.
- **Partial coverage:** provide the named optional dataset. Do not interpret Partial as a clean result.
- **Restore rejected:** the source failed SQLite integrity or schema checks; the active database remains untouched.

