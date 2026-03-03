# app/main.py

import time
from fastapi import FastAPI, HTTPException

from app.config import settings
from app.models import LeadGenRequest, LeadGenResponse

from app.sources.csv_source import load_leads_from_csv
from app.sources.directory_stub import fetch_from_directory
from app.sources.serpapi_source import fetch_from_serpapi

from app.utils.email_discover import find_email_from_website
from app.utils.email_verify import verify_email_basic
from app.utils.export import export_leads_csv

from app.agent.qualify import qualify_lead
from app.agent.outreach import generate_outreach_email
from app.utils.dedupe import dedupe_leads


app = FastAPI(title="AI Lead Agent", version="0.3.0")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/run", response_model=LeadGenResponse)
def run_agent(req: LeadGenRequest):
    t0 = time.time()

    # 1) Fetch leads
    if req.source == "csv":
        if not req.csv_path:
            raise HTTPException(status_code=400, detail="csv_path is required for source=csv")
        leads = load_leads_from_csv(req.csv_path, req.niche, req.location, req.limit)

    elif req.source == "serpapi":
        if not settings.serpapi_api_key:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "SERPAPI_API_KEY missing or not loaded",
                    "hint": "Ensure .env is in project root and restart uvicorn",
                },
            )
        leads = fetch_from_serpapi(req.niche, req.location, req.limit, settings.serpapi_api_key)

    elif req.source == "directory_stub":
        leads = fetch_from_directory(req.niche, req.location, req.limit)

    else:
        raise HTTPException(status_code=400, detail="Invalid source")

    # 2) Optional: discover emails from websites
    if getattr(req, "discover_emails", False):
        for lead in leads:
            if not lead.email and lead.website:
                try:
                    lead.email = find_email_from_website(lead.website)
                except Exception:
                    # never fail the whole run because one website is broken
                    pass

    # 3) Email verification pass (format + MX)
    for lead in leads:
        if lead.email:
            try:
                valid, reason = verify_email_basic(lead.email)
                lead.email_valid = valid
                lead.email_validation_reason = reason
            except Exception:
                lead.email_valid = False
                lead.email_validation_reason = "error"
    # 3.5) Deduplicate leads (important for agencies)
    leads = dedupe_leads(leads)

    # 4) Qualify + generate outreach for qualified leads
    processed = []
    for lead in leads:
        lead = qualify_lead(lead)
        if lead.qualified:
            lead = generate_outreach_email(lead)
        processed.append(lead)

    # 5) Export
    out_file = export_leads_csv(processed, "outputs/leads.csv")

    qualified_count = sum(1 for l in processed if l.qualified)
    elapsed = round(time.time() - t0, 2)

    return LeadGenResponse(
        niche=req.niche,
        location=req.location,
        count=len(processed),
        leads=processed,
        meta={
            "export_csv": out_file,
            "elapsed_sec": elapsed,
            "qualified_count": qualified_count,
            "source": req.source,
            "discover_emails": bool(getattr(req, "discover_emails", False)),
        },
    )