import re
from typing import List, Dict, Any
from .base import CheckOutcome

def check_regex_policy(text: str, required: List[str] | None = None, forbidden: List[str] | None = None) -> CheckOutcome:
    required = required or []
    forbidden = forbidden or []
    missing = []
    hits = []
    for pat in required:
        if not re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE):
            missing.append(pat)
    for pat in forbidden:
        if re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE):
            hits.append(pat)
    passed = (len(missing) == 0) and (len(hits) == 0)
    score = 1.0 if passed else 0.0
    return CheckOutcome(type="regex_policy", score=score, passed=passed, details={"missing": missing, "forbidden_hits": hits})
