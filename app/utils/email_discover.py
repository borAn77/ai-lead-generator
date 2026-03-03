import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)

def _same_domain(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.replace("www.", "") == urlparse(b).netloc.replace("www.", "")
    except Exception:
        return False

def _extract_emails(text: str) -> list[str]:
    return list(dict.fromkeys(EMAIL_RE.findall(text or "")))  # unique, stable order

def find_email_from_website(website: str, timeout: int = 12) -> str | None:
    if not website:
        return None

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(website, headers=headers, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
    except Exception:
        return None

    html = r.text or ""
    emails = _extract_emails(html)
    if emails:
        return emails[0]

    # Try common pages (contact / about / imprint)
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        text = (a.get_text() or "").lower()
        if "contact" in href.lower() or "kontakt" in href.lower() or "impressum" in href.lower() or "about" in href.lower():
            candidates.append(urljoin(website, href))
        elif any(k in text for k in ["contact", "kontakt", "impressum", "about"]):
            candidates.append(urljoin(website, href))

    # keep only same-domain + first few
    filtered = []
    for url in candidates:
        if _same_domain(website, url):
            filtered.append(url)
    filtered = list(dict.fromkeys(filtered))[:3]

    for url in filtered:
        try:
            rr = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if rr.status_code >= 400:
                continue
            emails = _extract_emails(rr.text or "")
            if emails:
                return emails[0]
        except Exception:
            continue

    return None