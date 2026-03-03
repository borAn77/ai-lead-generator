from typing import List
from app.models import Lead


def dedupe_leads(leads: List[Lead]) -> List[Lead]:
    """
    Remove duplicates by:
    - email (strongest)
    - website domain
    - business name fallback
    """

    seen_emails = set()
    seen_domains = set()
    seen_names = set()

    clean = []

    for lead in leads:
        email = (lead.email or "").lower().strip()
        website = (lead.website or "").lower().strip()
        name = (lead.business_name or "").lower().strip()

        domain = ""
        if website:
            try:
                domain = website.split("//")[-1].split("/")[0].replace("www.", "")
            except Exception:
                domain = website

        # priority: email
        if email and email in seen_emails:
            continue

        # next: domain
        if domain and domain in seen_domains:
            continue

        # fallback: name
        if name and name in seen_names:
            continue

        if email:
            seen_emails.add(email)
        if domain:
            seen_domains.add(domain)
        if name:
            seen_names.add(name)

        clean.append(lead)

    return clean