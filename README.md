# 🛰️ AI-Sentinel

> **Evaluate · Monitor · Guard your AI systems**  
> Self-hosted evaluation & monitoring service for LLM outputs.  
> Built with **FastAPI + Postgres/pgvector + Tailwind dashboard**.

---

## 🚨 Why AI-Sentinel?

LLMs don’t fail loudly — they **hallucinate, regress, or leak data** silently.  
**AI-Sentinel** is your watchdog: it continuously **evaluates, monitors, and guards** your AI outputs.

- **Evaluate** → Run regression tests against your own datasets & model endpoints  
- **Monitor** → Score live production outputs in real-time  
- **Guard** → Detect JSON errors, PII leaks, missing citations, hallucinations, and unsafe outputs  
- **Track** → Pin baselines and diff model versions for regressions  

---

## 🔍 How AI-Sentinel compares

| Tool         | Hosting      | Checks out-of-box              | UI/Dashboard | Cost model          | Notes                                    |
|--------------|-------------|--------------------------------|--------------|--------------------|------------------------------------------|
| **AI-Sentinel** | Self-hosted | JSON validity, regex, PII, length, similarity, toxicity stub | ✅ Tailwind dashboard | Free (your infra only) | API-first, lightweight, works with any model |
| LangSmith    | SaaS        | Many, incl. custom evals       | ✅ Polished   | Paid per trace      | Deep LangChain integration, vendor lock-in |
| TruLens      | Lib + SaaS  | Attribution, scoring           | Limited      | Free + SaaS tiers   | Python-first, less monitoring focus        |
| Ragas        | Lib         | RAG-focused evals              | ❌ No UI     | Free (OSS)          | Python-only, no monitoring                 |
| Arize Phoenix| OSS         | Embedding metrics, drift       | ✅ Advanced   | Free OSS + SaaS     | Observability heavy, steeper learning curve|

👉 Choose **AI-Sentinel** if you want a **lean, open, self-hosted guardrail** for AI outputs — not another heavy SaaS with surprise trace bills.

---

## ✨ Current Features
- Project registration (dataset + inference endpoints)
- Run orchestration (pull dataset → call inference → run checks)
- Built-in checks:
  - ✅ JSON validity (with optional schema)
  - ✅ Regex policy (required / forbidden patterns)
  - ✅ PII detection (emails, phones, credit-cards, addresses)
  - ✅ Length bounds
  - ✅ Semantic similarity (optional, via OpenAI embeddings)
  - ✅ Toxicity (simple wordlist stub)
- Baseline management & regression diffs
- Monitoring endpoint (`/v1/monitor/events`)
- Minimal Tailwind dashboard for runs & stats

---

## 🛣️ Roadmap

### Near-term
- [ ] Dashboard filters, charts, and historical pass-rate trends  
- [ ] Prometheus metrics & healthcheck endpoints  
- [ ] Richer toxicity & safety classifiers  
- [ ] One-click demo mode (spawn dataset + inference inside service)  

### Mid-term
- [ ] CI/CD integration (GitHub Action for evals on PRs)  
- [ ] Slack/Teams alerts on regressions or prod failures  
- [ ] Pluggable check registry (drop in your own checks)  

### Long-term
- [ ] Multi-tenant SaaS mode (orgs, users, billing)  
- [ ] RAG-specific evals (faithfulness, context grounding)  
- [ ] Full compliance/audit reporting  

---

## 🚀 Quick Start

```bash
git clone https://github.com/yourname/ai-sentinel
cd ai-sentinel
docker compose up --build
```


  • Visit http://localhost:8000 → Dashboard
  • Visit http://localhost:8000/docs → Swagger API



🧪 Demo Mode

Point to the built-in demo endpoints:
  • Dataset: http://api:8000/demo/tests
  • Inference: http://api:8000/demo/infer


```
curl -X POST http://localhost:8000/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"demo","dataset_url":"http://api:8000/demo/tests","inference_url":"http://api:8000/demo/infer"}'
```

```
curl -X POST http://localhost:8000/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project-id>"}'
```

Then refresh the dashboard (/) or check GET /v1/runs/<id>/report.


## 🏗️ Architecture & Stack

AI-Sentinel is designed to stay **lean but extensible** — it’s not a research prototype glued together, and it’s not a monolith with a dozen moving parts. The stack is opinionated in a *“just enough infra”* way:

- **FastAPI** – one service, async-first, doubles as API and dashboard host. BackgroundTasks handle runs without dragging in Celery/Redis until you truly need them.  
- **Postgres + pgvector** – one database does it all: relational state, results, and (optionally) embeddings for semantic similarity. No dual-store complexity.  
- **SQLAlchemy 2.0 (async)** – modern ORM patterns, type hints, and clean schema migrations when you grow.  
- **Tailwind dashboard** – not a toy Swagger screen, but not an enterprise BI monster either; just enough UX to see runs, pass rates, and recent regressions at a glance.  
- **Checks as Python modules** – each check (JSON validity, regex, PII, similarity, etc.) is a self-contained function returning a structured outcome. Easy to extend, drop in, or disable via thresholds.  
- **httpx clients** – clean async calls to your dataset & inference endpoints; HMAC signing optional for real-world pipelines.  

The result: you get **one containerized service + one database** that can run on a laptop, in CI, or on a production cluster. It’s small enough to understand in an afternoon, but structured so you can evolve it into a team-grade system (add a worker, plug into Prometheus, wire Slack alerts) without rewrites.


📜 License

MIT
---


