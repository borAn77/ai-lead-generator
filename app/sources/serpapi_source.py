import requests
from typing import List
from app.models import Lead

SERPAPI_URL = "https://serpapi.com/search.json"

def fetch_from_serpapi(niche: str, location: str, limit: int, api_key: str) -> List[Lead]:
    params = {
        "engine": "google_maps",
        "q": f"{niche} in {location}",
        "type": "search",
        "api_key": api_key,
    }

    r = requests.get(SERPAPI_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()

    results = data.get("local_results", []) or []
    leads: List[Lead] = []

    for item in results[:limit]:
        name = (item.get("title") or "").strip()
        if not name:
            continue

        leads.append(
            Lead(
                business_name=name,
                website=item.get("website") or None,
                phone=item.get("phone") or None,
                city=location,
                niche=niche,
                email=None,  # we’ll optionally discover it from website next
            )
        )

    return leads