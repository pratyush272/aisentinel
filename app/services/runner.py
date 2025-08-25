import asyncio
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ..models import Project, Run, Sample, CheckResult
from .client import fetch_dataset, call_inference
from ..checks.json_validity import check_json_validity
from ..checks.regex_policy import check_regex_policy
from ..checks.length_bounds import check_length_bounds
from ..checks.pii import check_pii
from ..checks.similarity import check_similarity
from ..checks.base import CheckOutcome

DEFAULT_THRESHOLDS: Dict[str, Any] = {
    "json": {"enabled": False, "schema": None},
    "regex": {"required": [], "forbidden": []},
    "length": {"min": 10, "max": 3000},
    "pii": {"enabled": True},
    "similarity": {"enabled": False, "threshold": 0.82},
    "toxicity": {"enabled": False},  # stub only
}

async def execute_run(session_factory, run_id: str):
    # Create fresh session inside background task
    async with session_factory() as session:  # type: AsyncSession
        run = await session.get(Run, run_id)
        if not run:
            return
        project = await session.get(Project, run.project_id)
        if not project or not project.dataset_url or not project.inference_url:
            run.status = "failed"
            await session.commit()
            return
        run.status = "running"
        run.started_at = datetime.utcnow()
        await session.commit()

        thresholds = DEFAULT_THRESHOLDS.copy()
        if project.thresholds_json:
            # shallow merge
            thresholds.update({**thresholds, **project.thresholds_json})

        # Fetch dataset
        try:
            dataset = await fetch_dataset(
                project.dataset_url,
                headers=project.headers_json or None,
                limit=100 if run.tag is None else 100,
                offset=0,
                tag=run.tag,  # use run.tag as dataset tag by default
            )
        except Exception as e:
            run.status = "failed"
            run.totals_json = {"error": f"dataset_fetch_failed: {e}"}
            await session.commit()
            return

        # Iterate tests
        total = 0
        for item in dataset:
            test_id = str(item.get("id"))
            prompt = item.get("prompt", "")
            reference = item.get("reference")
            metadata = item.get("metadata", {})

            # Call inference
            payload = {"id": test_id, "prompt": prompt, "metadata": metadata}
            try:
                resp = await call_inference(
                    project.inference_url,
                    payload=payload,
                    headers=project.headers_json or None,
                    hmac_secret=project.hmac_secret,
                )
            except Exception as e:
                # Create sample with failure info
                sample = Sample(
                    run_id=run.id,
                    test_id=test_id,
                    prompt=prompt,
                    output=f"__ERROR__: inference_failed: {e}",
                    reference_json=reference,
                    latency_ms=None,
                    tokens=None,
                )
                session.add(sample)
                await session.flush()
                await _persist_checks_for_error(session, sample, str(e))
                total += 1
                continue

            output = str(resp.get("output", ""))
            latency_ms = resp.get("latency_ms")
            tokens = resp.get("tokens")

            sample = Sample(
                run_id=run.id,
                test_id=test_id,
                prompt=prompt,
                output=output,
                reference_json=reference,
                latency_ms=latency_ms,
                tokens=tokens,
            )
            session.add(sample)
            await session.flush()

            # Run checks
            await _run_checks(session, sample, output, reference, thresholds)

            total += 1

        run.status = "done"
        run.finished_at = datetime.utcnow()
        run.totals_json = {"samples": total}
        await session.commit()

async def _persist_checks_for_error(session: AsyncSession, sample: Sample, err: str):
    # Minimal checks: mark as failed for length and json validity
    outcomes = [
        CheckOutcome("length_bounds", 0.0, False, {"error": err}),
        CheckOutcome("json_validity", 0.0, False, {"error": err}),
    ]
    for oc in outcomes:
        session.add(CheckResult(sample_id=sample.id, type=oc.type, score=oc.score, passed=oc.passed, details_json=oc.details))
    await session.flush()

async def _run_checks(session: AsyncSession, sample: Sample, output: str, reference: Any, thresholds: Dict[str, Any]):
    outcomes: List[CheckOutcome] = []

    # length
    lcfg = thresholds.get("length", {})
    outcomes.append(check_length_bounds(output, min_chars=int(lcfg.get("min", 10)), max_chars=int(lcfg.get("max", 3000))))

    # json
    jcfg = thresholds.get("json", {})
    if jcfg.get("enabled", False):
        outcomes.append(check_json_validity(output, schema=jcfg.get("schema")))

    # regex policy
    rcfg = thresholds.get("regex", {})
    outcomes.append(check_regex_policy(output, required=rcfg.get("required", []), forbidden=rcfg.get("forbidden", [])))

    # pii
    if thresholds.get("pii", {}).get("enabled", True):
        outcomes.append(check_pii(output))

    # similarity
    scfg = thresholds.get("similarity", {})
    if scfg.get("enabled", False):
        ref_text = None
        if isinstance(reference, dict):
            ref_text = reference.get("reference_text")
        elif isinstance(reference, str):
            ref_text = reference
        outcomes.append(await check_similarity(output, ref_text, threshold=float(scfg.get("threshold", 0.82))))

    # (optional) toxicity stub - simple wordlist
    if thresholds.get("toxicity", {}).get("enabled", False):
        tox_words = ["idiot", "stupid", "hate"]
        found = [w for w in tox_words if w in (output or "").lower()]
        passed = len(found) == 0
        outcomes.append(CheckOutcome("toxicity", 1.0 if passed else 0.0, passed, {"hits": found}))

    for oc in outcomes:
        session.add(CheckResult(sample_id=sample.id, type=oc.type, score=oc.score, passed=oc.passed, details_json=oc.details))

    await session.flush()
