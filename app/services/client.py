import json
import httpx
from typing import Any, Dict, List, Optional, Tuple
from ..utils.security import hmac_signature

async def fetch_dataset(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    limit: int = 100,
    offset: int = 0,
    tag: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params = {"limit": limit, "offset": offset}
    if tag:
        params["tag"] = tag
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        content_type = r.headers.get("content-type", "")
        text = r.text
        # Support JSON array or NDJSON
        if "application/json" in content_type or text.strip().startswith("["):
            return r.json()
        # NDJSON / JSONL
        items = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
        return items

async def call_inference(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    hmac_secret: Optional[str] = None,
) -> Dict[str, Any]:
    body = json.dumps(payload).encode()
    send_headers = dict(headers or {})
    if hmac_secret:
        sig = hmac_signature(hmac_secret, body)
        if sig:
            send_headers["X-Signature"] = sig
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, content=body, headers={**send_headers, "Content-Type": "application/json"})
        r.raise_for_status()
        return r.json()
