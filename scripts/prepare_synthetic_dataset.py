from __future__ import annotations

import csv
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "demo" / "claims_demo_synthetic.csv"
RENAME = {
    "claim_amount_requested_inr": "claim_amount_requested_aed",
    "claim_amount_approved_inr": "claim_amount_approved_aed",
}


def rename_currency_labels(path: Path = SOURCE) -> bool:
    temporary = path.with_suffix(".aed-label.tmp")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        header = next(reader)
        renamed = [RENAME.get(column, column) for column in header]
        if renamed == header:
            return False
        with temporary.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target, lineterminator="\n")
            writer.writerow(renamed)
            writer.writerows(reader)
    os.replace(temporary, path)
    return True


if __name__ == "__main__":
    changed = rename_currency_labels()
    print("Renamed synthetic amount labels from INR to AED." if changed else "Synthetic amount labels already use AED.")
