from openai import OpenAI
from app.config import settings
from app.models import Lead

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM = """You are a lead qualification assistant for a marketing agency.
Score each lead 0-100 and decide if it is worth outreach.
Focus on: clear business identity, contactability (email/website), local intent, and fit for marketing services.
Return strict JSON only.
"""

def qualify_lead(lead: Lead) -> Lead:
    if not settings.openai_api_key:
        # No key -> simple heuristic fallback
        score = 70 if (lead.website or lead.email) else 40
        lead.score = score
        lead.qualified = score >= 60
        lead.qualification_reason = "Heuristic scoring (no OpenAI key)."
        return lead

    payload = {
        "business_name": lead.business_name,
        "website": lead.website,
        "email": lead.email,
        "phone": lead.phone,
        "city": lead.city,
        "niche": lead.niche,
    }

    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Lead data: {payload}\n\nReturn JSON: {{score:int, qualified:bool, reason:str}}"},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content.strip()

    # Minimal safe parse (avoid crashing on non-JSON)
    import json
    try:
        data = json.loads(content)
    except Exception:
        lead.score = 0
        lead.qualified = False
        lead.qualification_reason = f"Model returned non-JSON: {content[:200]}"
        return lead

    lead.score = int(data.get("score", 0))
    lead.qualified = bool(data.get("qualified", False))
    lead.qualification_reason = str(data.get("reason", "")).strip()
    return lead