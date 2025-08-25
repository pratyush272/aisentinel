from collections import defaultdict
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Run, Sample, CheckResult, Project

async def build_report(session: AsyncSession, run_id: str) -> Dict[str, Any]:
    run = await session.get(Run, run_id)
    if not run:
        raise ValueError("Run not found")
    proj = await session.get(Project, run.project_id)

    res_samples = await session.execute(select(Sample).where(Sample.run_id == run_id))
    samples = res_samples.scalars().all()
    sample_ids = [s.id for s in samples]

    res_checks = await session.execute(select(CheckResult).where(CheckResult.sample_id.in_(sample_ids)))
    checks = res_checks.scalars().all()

    total_checks = len(checks) or 1
    passed_checks = sum(1 for c in checks if c.passed)
    pass_rate = passed_checks / total_checks

    by_check = defaultdict(lambda: {"passed": 0, "total": 0})
    failures: List[Dict[str, Any]] = []

    for c in checks:
        by_check[c.type]["total"] += 1
        if c.passed:
            by_check[c.type]["passed"] += 1
        else:
            failures.append({
                "sample_id": c.sample_id,
                "type": c.type,
                "score": c.score,
                "details": c.details_json,
            })

    by_check_rates = {k: {"pass_rate": (v["passed"] / v["total"]) if v["total"] else 0.0, "total": v["total"]} for k, v in by_check.items()}
    totals = {"samples": len(samples), "checks": total_checks, "passed": passed_checks}

    baseline_diff = None
    if proj and proj.baseline_run_id and proj.baseline_run_id != run_id:
        baseline_diff = await diff_against_baseline(session, baseline_run_id=proj.baseline_run_id, current_run_id=run_id)

    return {
        "run_id": run_id,
        "project_id": run.project_id,
        "pass_rate": pass_rate,
        "totals": totals,
        "by_check": by_check_rates,
        "failures": failures[:200],  # cap
        "baseline_diff": baseline_diff,
    }

async def diff_against_baseline(session: AsyncSession, baseline_run_id: str, current_run_id: str) -> Dict[str, Any]:
    # Compare pass/fail per (test_id, check_type)
    from sqlalchemy import select
    from ..models import Sample, CheckResult

    # Baseline
    bs_samples = (await session.execute(select(Sample).where(Sample.run_id == baseline_run_id))).scalars().all()
    bmap = {s.test_id: s.id for s in bs_samples}
    bchecks = (await session.execute(select(CheckResult).where(CheckResult.sample_id.in_([s.id for s in bs_samples])))).scalars().all()
    bstatus = {(c.sample_id, c.type): c.passed for c in bchecks}
    # Current
    csamples = (await session.execute(select(Sample).where(Sample.run_id == current_run_id))).scalars().all()
    cmap = {s.test_id: s.id for s in csamples}
    cchecks = (await session.execute(select(CheckResult).where(CheckResult.sample_id.in_([s.id for s in csamples])))).scalars().all()
    cstatus = {(c.sample_id, c.type): c.passed for c in cchecks}

    regressions = 0
    improvements = 0
    pairs = []

    # Align by test_id and check type via reference mapping
    # Build maps test_id -> {type -> passed}
    from collections import defaultdict
    b_by_test = defaultdict(dict)
    for c in bchecks:
        b_by_test[next(sid for sid, tid in bmap.items() if tid == c.sample_id)][c.type] = c.passed  # reverse lookup
    # but reverse lookup above is expensive; better: build sample_id->test_id map
    sid_to_tid_b = {s.id: s.test_id for s in bs_samples}
    sid_to_tid_c = {s.id: s.test_id for s in csamples}
    b_by_test = defaultdict(dict)
    for c in bchecks:
        b_by_test[sid_to_tid_b[c.sample_id]][c.type] = c.passed
    c_by_test = defaultdict(dict)
    for c in cchecks:
        c_by_test[sid_to_tid_c[c.sample_id]][c.type] = c.passed

    for tid, btypes in b_by_test.items():
        if tid not in c_by_test:
            continue
        for t, bpass in btypes.items():
            if t not in c_by_test[tid]:
                continue
            cpass = c_by_test[tid][t]
            if bpass and not cpass:
                regressions += 1
                pairs.append({"test_id": tid, "check": t, "from": True, "to": False})
            elif not bpass and cpass:
                improvements += 1
                pairs.append({"test_id": tid, "check": t, "from": False, "to": True})

    return {"regressions": regressions, "improvements": improvements, "examples": pairs[:200]}
