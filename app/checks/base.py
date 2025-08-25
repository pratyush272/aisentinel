from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class CheckOutcome:
    type: str
    score: float
    passed: bool
    details: Dict[str, Any]
