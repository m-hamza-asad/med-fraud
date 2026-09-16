# Demo Script

1. Run `.\scripts\demo-reset.ps1`, choose fresh disposable passwords when prompted, then run `.\scripts\start.ps1`.
2. Sign in as `admin` with the password you just configured.
3. Open Upload & validation and observe committed `canonical-demo-claims.csv` history.
4. Use the API or upload the generated demo CSV, then create an evaluation for its batch at `2026-09-15`.
5. Open Claims: compare the flagged, clean, and partial-data examples. Drill into the flagged claim and inspect the rule/version/evidence snapshot.
6. Open Providers and Networks to verify distinct associated amounts and explicit boundaries.
7. Open Rules: confirm 164 total, 149 executable, 12 deferred, and 3 excluded.
8. Create an Admin threshold version; verify old results are unchanged. Sign in as Analyst and confirm the API rejects the same write.
9. Generate CSV, Excel, and PDF in Reports.
10. Run backup, demo reset, and restore scripts; compare key counts.
