import re
import dns.resolver

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def is_valid_format(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_RE.match(email))


def has_mx_record(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return len(answers) > 0
    except Exception:
        return False


def verify_email_basic(email: str) -> tuple[bool, str]:
    """
    Returns: (is_valid, reason)
    """
    if not email:
        return False, "missing"

    if not is_valid_format(email):
        return False, "bad_format"

    domain = email.split("@")[-1].lower()

    if not has_mx_record(domain):
        return False, "no_mx"

    return True, "ok"