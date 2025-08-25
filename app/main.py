import os
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, cast, Integer
from dotenv import load_dotenv

from .database import get_session, init_db, SessionLocal
from . import models
from . import schemas
from .services.runner import execute_run
from .services.report import build_report

load_dotenv()

app = FastAPI(title="LLM Eval Service", version="0.1.0")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.post("/v1/projects", response_model=schemas.ProjectOut)
async def create_project(payload: schemas.ProjectCreate, session: AsyncSession = Depends(get_session)):
    proj = models.Project(
        name=payload.name,
        dataset_url=payload.dataset_url,
        inference_url=payload.inference_url,
        headers_json=payload.headers,
        hmac_secret=payload.hmac_secret,
        thresholds_json=payload.thresholds,
    )
    session.add(proj)
    await session.commit()
    return schemas.ProjectOut(id=proj.id, name=proj.name, dataset_url=proj.dataset_url, inference_url=proj.inference_url, baseline_run_id=proj.baseline_run_id)

@app.post("/v1/runs", response_model=schemas.RunOut)
async def start_run(payload: schemas.RunCreate, background: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    # Ensure project exists
    proj = await session.get(models.Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")

    run = models.Run(project_id=payload.project_id, tag=payload.dataset_tag or payload.tag, status="queued")
    session.add(run)
    await session.commit()

    # Launch background execution with a fresh session factory
    background.add_task(execute_run, SessionLocal, run.id)

    return schemas.RunOut(id=run.id, project_id=run.project_id, tag=run.tag, status=run.status)

@app.get("/v1/runs/{run_id}/report", response_model=schemas.ReportOut)
async def get_report(run_id: str, session: AsyncSession = Depends(get_session)):
    report = await build_report(session, run_id)
    return schemas.ReportOut(**report)

@app.post("/v1/projects/{project_id}/baseline")
async def set_baseline(project_id: str, payload: schemas.BaselineSet, session: AsyncSession = Depends(get_session)):
    proj = await session.get(models.Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")
    run = await session.get(models.Run, payload.run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(status_code=400, detail="invalid run for this project")
    proj.baseline_run_id = run.id
    await session.commit()
    return {"ok": True, "project_id": project_id, "baseline_run_id": run.id}

# Optional: monitoring endpoint (no persistence by default)
from .checks.json_validity import check_json_validity
from .checks.regex_policy import check_regex_policy
from .checks.length_bounds import check_length_bounds
from .checks.pii import check_pii

@app.post("/v1/monitor/events")
async def monitor_event(payload: schemas.MonitorEvent, session: AsyncSession = Depends(get_session)):
    # Pull thresholds from project
    proj = await session.get(models.Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")
    thresholds = (proj.thresholds_json or {})
    length_cfg = thresholds.get("length", {"min": 10, "max": 3000})
    regex_cfg = thresholds.get("regex", {"required": [], "forbidden": []})
    json_cfg = thresholds.get("json", {"enabled": False, "schema": None})
    pii_cfg = thresholds.get("pii", {"enabled": True})

    outs = []
    outs.append(check_length_bounds(payload.output, min_chars=int(length_cfg.get("min",10)), max_chars=int(length_cfg.get("max", 3000))).__dict__)
    if json_cfg.get("enabled", False):
        outs.append(check_json_validity(payload.output, schema=json_cfg.get("schema")).__dict__)
    outs.append(check_regex_policy(payload.output, required=regex_cfg.get("required", []), forbidden=regex_cfg.get("forbidden", [])).__dict__)
    if pii_cfg.get("enabled", True):
        outs.append(check_pii(payload.output).__dict__)

    return {"checks": outs}

from starlette.templating import Jinja2Templates
from sqlalchemy import func

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    # Stats
    projects = (await session.execute(select(func.count(models.Project.id)))).scalar_one()
    runs = (await session.execute(select(func.count(models.Run.id)))).scalar_one()
    # Grab recent runs and compute quick pass rates
    res = await session.execute(select(models.Run, models.Project).join(models.Project, models.Run.project_id == models.Project.id).order_by(models.Run.started_at.desc().nullslast()).limit(20))
    rows = []
    from .models import CheckResult, Sample
    for run, proj in res.all():
        # pass rate for this run
        if run.status != 'done':
            pr = None
        else:
            sres = await session.execute(select(Sample.id).where(Sample.run_id == run.id))
            sids = [sid for (sid,) in sres.all()]
            if sids:
                cres = await session.execute(
                    select(
                        func.sum(cast(CheckResult.passed, Integer)),
                        func.count(CheckResult.id),
                    ).where(CheckResult.sample_id.in_(sids))
                )
                passed, total = cres.one()
                pr = (passed or 0) / (total or 1)
            else:
                pr = 0.0
        rows.append({"run": run, "project": proj, "pass_rate": pr})
    # avg of recent pass rates (ignore None)
    pr_values = [r["pass_rate"] for r in rows if r["pass_rate"] is not None]
    avg_pass = sum(pr_values)/len(pr_values) if pr_values else None
    stats = {"projects": projects, "runs": runs, "avg_pass": avg_pass}
    return templates.TemplateResponse("dashboard.html", {"request": request, "runs": rows, "stats": stats})

# --- Demo endpoints ---
from pydantic import BaseModel

class DemoInferIn(BaseModel):
    id: str
    prompt: str
    metadata: dict | None = None

@app.get("/demo/tests")
async def demo_tests():
    return [
        {"id": "t-001", "prompt": "Explain our refund policy in 2 sentences.", "reference": {"reference_text": "Refunds within 30 days with proof of purchase."}},
        {"id": "t-002", "prompt": "Summarize the privacy policy; include a citation.", "reference": {"reference_text": "We do not sell personal data; users can request deletion."}},
        {"id": "t-003", "prompt": "Return a JSON object with keys: status, eta_days.", "reference": {"reference_text": "{""status"": ""ok"", ""eta_days"": 5}"}},
    ]

@app.post("/demo/infer")
async def demo_infer(body: DemoInferIn):
    import time
    start = time.time()
    p = body.prompt.lower()
    # Very naive generation for demo purposes
    if "json" in p:
        output = '{"status":"ok","eta_days":5}'
    elif "citation" in p or "cite" in p:
        output = "According to our policy (https://example.com/policy), we process data responsibly."
    else:
        output = "We offer refunds within 30 days if you have proof of purchase. Contact support for assistance."
    latency_ms = int((time.time() - start) * 1000) + 50
    tokens = max(10, len(output.split()))
    return {"output": output, "latency_ms": latency_ms, "tokens": tokens}
