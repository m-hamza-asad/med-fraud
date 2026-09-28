# Shahai Medical Payment Integrity POC

Local, browser-based decision support for tokenized UAE medical claims. The app shows `Flagged` or `No flag detected` together with `Complete` or `Partial` evaluation coverage; it never labels a person or claim as fraudulent.

> Current release status: see `IMPLEMENTATION_STATUS.md`. The evaluator uses canonical facts, governed references, explicit exclusions, and versioned configuration; caller-supplied rule booleans and synthetic labels are discarded. Local defaults remain engineering assumptions rather than approved payer policy.

## Prerequisites and first run

- Windows 10/11 with PowerShell 7 recommended.
- Node.js 24 (the current target-machine version).
- Python 3.12/3.13, or the Codex bundled Python path detected by setup.
- Internet is needed only during initial dependency installation; normal operation is local.

```powershell
Set-Location 'C:\Users\Yoga 9\OneDrive\Desktop\Shahai Product Development\Med Fraud'
.\scripts\setup.ps1
.\scripts\start.ps1
```

Setup prompts for initial passwords for the seeded `admin` and `analyst` usernames and stores only Argon2 hashes. Open the exact `http://127.0.0.1:<port>` printed by the start script. Stop only the recorded project processes with:

```powershell
.\scripts\stop.ps1
```

## Demo and verification

```powershell
.\scripts\demo-reset.ps1
.\scripts\test.ps1
```

The disposable demo reset prompts for fresh passwords, backs up an existing database, regenerates templates, and loads three synthetic claims. See `docs/DEMO_SCRIPT.md`.

## Data and privacy boundary

Use tokenized opaque identifiers only. Runtime databases, uploads, reports, backups, and credentials are ignored. The service binds to `127.0.0.1`; there is no telemetry or required runtime internet connection. This POC is not a compliance certification or autonomous adjudication system.
