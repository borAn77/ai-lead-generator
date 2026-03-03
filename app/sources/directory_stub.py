from typing import List
from app.models import Lead

def fetch_from_directory(niche: str, location: str, limit: int) -> List[Lead]:
    """
    Replace this with:
    - SerpAPI / Apify / RapidAPI / your own scraper
    - Or any business directory you can legally access.
    """
    # Dummy data to prove the pipeline works end-to-end:
    sample = [
        Lead(business_name=f"{niche.title()} Prospects {i+1}", city=location, niche=niche, website=None, email=None)
        for i in range(min(limit, 10))
    ]
    return sample