from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = [*sorted((ROOT / "apps" / "api" / "medfraud").glob("*.py")), *sorted((ROOT / "apps" / "web" / "src").glob("*.tsx"))]
forbidden = {
    "caller signal lookup": re.compile(r"signals\s*\.\s*get|signals\s*\[") ,
    "hard-coded bearer secret": re.compile(r"Bearer\s+[A-Za-z0-9_-]{20,}"),
    "dangerous HTML injection": re.compile(r"dangerouslySetInnerHTML"),
}
failures = []
for path in PRODUCTION:
    text = path.read_text(encoding="utf-8")
    for label, pattern in forbidden.items():
        if pattern.search(text): failures.append(f"{label}: {path.relative_to(ROOT)}")
if failures:
    raise SystemExit("Security check failed:\n" + "\n".join(failures))
print(f"Security check passed across {len(PRODUCTION)} production source files.")
