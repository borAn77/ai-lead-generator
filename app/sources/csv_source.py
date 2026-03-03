import csv
from typing import List
from app.models import Lead

def load_leads_from_csv(path: str, niche: str, location: str, limit: int) -> List[Lead]:
    leads: List[Lead] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            business_name = (row.get("business_name") or "").strip()
            if not business_name:
                continue
            leads.append(
                Lead(
                    business_name=business_name,
                    website=(row.get("website") or "").strip() or None,
                    email=(row.get("email") or "").strip() or None,
                    phone=(row.get("phone") or "").strip() or None,
                    city=(row.get("city") or "").strip() or location,
                    niche=niche,
                )
            )
    return leads