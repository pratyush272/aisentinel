import hmac
import hashlib
from typing import Optional

def hmac_signature(secret: Optional[str], body: bytes) -> Optional[str]:
    if not secret:
        return None
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return sig
