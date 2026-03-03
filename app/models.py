from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any

class Lead(BaseModel):
    business_name: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    niche: Optional[str] = None
    

    qualified: Optional[bool] = None
    qualification_reason: Optional[str] = None
    outreach_email_subject: Optional[str] = None
    outreach_email_body: Optional[str] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    email_valid: Optional[bool] = None
    email_validation_reason: Optional[str] = None

class LeadGenRequest(BaseModel):
    niche: str
    location: str
    source: Literal["csv", "serpapi", "directory_stub"] = "csv"
    limit: int = Field(default=50, ge=1, le=500)
    csv_path: Optional[str] = "data/sample_leads.csv"
    discover_emails: bool = True  # <— add this

class LeadGenResponse(BaseModel):
    niche: str
    location: str
    count: int
    leads: List[Lead]
    meta: Dict[str, Any] = {}
    