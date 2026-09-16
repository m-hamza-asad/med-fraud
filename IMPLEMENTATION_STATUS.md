# Implementation Status

Last updated: 2026-09-15 (Asia/Karachi)

## Release status

**Not ready.** A working local foundation and demo UI now run, but the authoritative catalogue does not provide enough field-level policy to implement the required 149 real evaluators. No release gate is claimed as fully passed.

## Phases

| Gate | Scope | Status | Evidence / remaining work |
|---|---|---|---|
| 0 | Baseline, architecture, authentication, migrations, Shahai shell | Mostly complete | Local health, two users, token-based shell, setup/start/stop, tests and build verified. Formal migration revisions remain. |
| 1 | Canonical data, imports, templates, validation | Partial | Three Excel templates, CSV pack, checksum, five-year and transactional flat-claim intake exist; complete canonical datasets/relationships remain. |
| 2 | Registry, configuration, claim-level evaluation | Blocked on policy contracts | 164 registry and prospective configuration platform exist. Interim structured-fact adapter is not a substitute for 149 catalogue-semantic evaluators. |
| 3 | Historical and provider analytics | Not started | Pending Gate 2. |
| 4 | Network, pharmacy, policy, payment analytics | Not started | Pending Gate 3. |
| 5 | All 149 evaluators, reporting, polish, release QA | Not started | Pending prior gates. |

## Runtime baseline

- Windows / PowerShell workspace.
- Node.js: `v24.18.0`.
- npm: `11.16.0`.
- Python is not on `PATH`.
- Codex bundled Python: `C:\Users\Yoga 9\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`, version `3.12.14`.
- The bundled Python does not currently include FastAPI; a project virtual environment and locked dependencies are required.
- The folder is not currently a Git repository.

## Completed checks

| Check | Command | Result |
|---|---|---|
| Workspace inventory | `Get-ChildItem -Force` | Four supplied planning/specification files present; no implementation scaffold found. |
| Repository state | `git status --short --branch` | Not a Git repository; repository initialization is not treated as a blocker. |
| Node runtime | `node --version; npm --version` | `v24.18.0`; `11.16.0`. |
| Python runtime | bundled `python.exe --version` | `Python 3.12.14`. |
| Required Python baseline | bundled `python.exe -c "import fastapi"` | Fails: `ModuleNotFoundError`; dependencies not installed yet. |

## Current work

- Obtain business-owned field-level contracts for the 149 executable controls.
- Replace the disclosed structured-fact adapter with real family evaluators and full fixtures.
- Complete canonical entities, reports, E2E, performance, screenshot/PDF evidence, and release QA.

## Known failures / blockers

- The catalogue omits rule-level population, input fields, reason/evidence contracts and resolved dispositions for all/most controls; only nine rules name `cfg.*` parameters. Implementing exact payment policy would require inventing materially consequential business rules.
- Ten critical Playwright E2E workflows are not implemented or run.
- Required full historical/peer/network computations and performance benchmark against persisted 10,000-line history are not implemented.

## Exact commands used

```powershell
git status --short --branch
node --version
npm --version
python --version
py -0p
& 'C:\Users\Yoga 9\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' --version
& 'C:\Users\Yoga 9\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -c "import fastapi"
.\scripts\demo-reset.ps1
.\scripts\start.ps1
.\scripts\test.ps1
.\scripts\backup.ps1 -Destination '.\data\backups\verification.sqlite3'
.\scripts\stop.ps1
.\scripts\restore.ps1 -Source '.\data\backups\verification.sqlite3'
$env:PYTHONPATH = (Join-Path (Get-Location) 'apps\api'); .\.venv\Scripts\python.exe scripts\benchmark.py
```

## Latest verified results

- Backend: **155 passed** in 2.24 seconds.
- Frontend unit: **1 passed**.
- TypeScript strict check: **passed, 0 errors**.
- ESLint: **passed, 0 warnings/errors**.
- Vite production build: **passed**, 1.52 seconds.
- API health/startup: **ready**, SQLite ready, registry 149/12/3.
- Browser console after inspected workflows: **0 errors/warnings**.
- Visual inspection: sign-in, overview, claim detail, and rule registry at default/mobile and 1440×900; dark/light; fixed light-theme hero contrast and horizontal page overflow.
- Backup/stop/restore/start integrity sequence: **passed**.
- In-memory benchmark: 1,000-row validation 0.0046 s; 149,000 interim structured-contract evaluations 0.3333 s. This does not prove the required historical benchmark.
