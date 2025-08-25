import os
from typing import Optional, Dict, Any
import numpy as np
from .base import CheckOutcome

# Optional: OpenAI embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

async def _embed_openai(text: str) -> Optional[list[float]]:
    try:
        import httpx
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        payload = {"model": "text-embedding-3-small", "input": text}
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data["data"][0]["embedding"]
    except Exception:
        return None

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
    return float(np.dot(a, b) / denom)

async def check_similarity(output_text: str, reference_text: Optional[str], threshold: float = 0.82) -> CheckOutcome:
    if not reference_text:
        return CheckOutcome(type="similarity", score=1.0, passed=True, details={"skipped": True, "reason": "no_reference"})
    if not OPENAI_API_KEY:
        return CheckOutcome(type="similarity", score=0.0, passed=False, details={"error": "OPENAI_API_KEY not set"})
    out_emb = await _embed_openai(output_text)
    ref_emb = await _embed_openai(reference_text)
    if not out_emb or not ref_emb:
        return CheckOutcome(type="similarity", score=0.0, passed=False, details={"error": "embedding_failed"})
    sim = _cosine(np.array(out_emb), np.array(ref_emb))
    passed = sim >= threshold
    return CheckOutcome(type="similarity", score=sim, passed=passed, details={"similarity": sim, "threshold": threshold})
