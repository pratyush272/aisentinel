import re
from .base import CheckOutcome

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+\d{1,3}[- ]?)?\b\d{10}\b")
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")  # naive credit card-ish
ADDRESS_HINTS = ["street", "road", "lane", "avenue", "sector", "noida", "delhi", "bangalore"]

def check_pii(text: str) -> CheckOutcome:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    cards = CC_RE.findall(text)
    address_hits = [w for w in ADDRESS_HINTS if w.lower() in text.lower()]
    any_pii = bool(emails or phones or cards or address_hits)
    return CheckOutcome(
        type="pii",
        score=0.0 if any_pii else 1.0,
        passed=not any_pii,
        details={"emails": emails, "phones": phones, "cards": cards, "address_hints": address_hits},
    )
