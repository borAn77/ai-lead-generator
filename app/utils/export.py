import csv
from typing import List
from pathlib import Path
from app.models import Lead

def export_leads_csv(leads: List[Lead], out_path: str) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    rows = [l.model_dump() for l in leads]

    # keep columns stable
    fieldnames = sorted({k for r in rows for k in r.keys()})
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return out_path