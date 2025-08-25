import json
from typing import Any, Dict, Optional
from jsonschema import validate, ValidationError
from .base import CheckOutcome

def check_json_validity(text: str, schema: Optional[Dict[str, Any]] = None) -> CheckOutcome:
    try:
        obj = json.loads(text)
        if schema:
            try:
                validate(instance=obj, schema=schema)
            except ValidationError as e:
                return CheckOutcome(type="json_validity", score=0.0, passed=False, details={"error": str(e)})
        return CheckOutcome(type="json_validity", score=1.0, passed=True, details={"parsed": True})
    except Exception as e:
        return CheckOutcome(type="json_validity", score=0.0, passed=False, details={"error": str(e)})
