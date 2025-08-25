from .base import CheckOutcome

def check_length_bounds(text: str, min_chars: int = 1, max_chars: int = 5000) -> CheckOutcome:
    n = len(text or "")
    passed = (n >= min_chars) and (n <= max_chars)
    score = 1.0 if passed else 0.0
    return CheckOutcome(type="length_bounds", score=score, passed=passed, details={"length": n, "min": min_chars, "max": max_chars})
