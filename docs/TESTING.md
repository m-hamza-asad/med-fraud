# Testing

Run `.\scripts\test.ps1`. It runs backend tests, Python compilation, frontend unit tests, strict TypeScript checking, ESLint, and the production build, and fails immediately on any non-zero native command.

Run `npm --prefix apps/web run test:e2e` for the isolated authenticated browser workflow, keyboard/landmark checks, responsive overflow check, and desktop/mobile visual comparisons. The E2E database is kept under ignored `.test-artifacts`.

The parameterized evaluator matrix covers all 149 executable IDs for triggered, clean negative/boundary, missing input, and exclusion behavior. Dedicated tests cover signal/outcome quarantine, preview-no-mutation and idempotent commit, migrations, robust peer methods, graph boundary/reconciliation, and export reconciliation. `scripts/benchmark.py`, `scripts/profile_dataset.py`, and `scripts/security_check.py` provide measured performance, aggregate-safe profiling, and static security gates.

