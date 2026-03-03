from openai import OpenAI
from app.config import settings
from app.models import Lead

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM = """You write short, high-response cold emails for marketing agencies.
Rules:
- 90-140 words
- 1 clear CTA
- No hype, no spam, no emojis
- Make it feel human
Return strict JSON only.
"""

def generate_outreach_email(lead: Lead) -> Lead:
    if not settings.openai_api_key:
        lead.outreach_email_subject = f"Quick idea for {lead.business_name}"
        lead.outreach_email_body = (
            f"Hi {lead.business_name} team,\n\n"
            f"I noticed you operate in {lead.city}. I help {lead.niche} businesses get more booked calls using simple website + ads optimizations.\n\n"
            f"If I send 2-3 quick improvement ideas tailored to your current setup, would that be useful?\n\n"
            f"Best,\nBoran"
        )
        return lead

    prompt = {
        "business_name": lead.business_name,
        "niche": lead.niche,
        "city": lead.city,
        "website": lead.website,
    }

    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Write outreach for this lead: {prompt}\n\nReturn JSON: {{subject:str, body:str}}"},
        ],
        temperature=0.4,
    )

    content = (resp.choices[0].message.content or "").strip()

    import json
    try:
        data = json.loads(content)
        lead.outreach_email_subject = str(data.get("subject", "")).strip()
        lead.outreach_email_body = str(data.get("body", "")).strip()
    except Exception:
        lead.outreach_email_subject = "Quick question"
        lead.outreach_email_body = content[:500]

    return lead