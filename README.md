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


  • Visit http://localhost:8000 → Dashboard
  • Visit http://localhost:8000/docs → Swagger API



🧪 Demo Mode

Point to the built-in demo endpoints:
  • Dataset: http://api:8000/demo/tests
  • Inference: http://api:8000/demo/infer



curl -X POST http://localhost:8000/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"demo","dataset_url":"http://api:8000/demo/tests","inference_url":"http://api:8000/demo/infer"}'

curl -X POST http://localhost:8000/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project-id>"}'


Then refresh the dashboard (/) or check GET /v1/runs/<id>/report.



📜 License

MIT
---

⚡ This positions **AI-Sentinel** as a *self-hosted, lean alternative to LangSmith & friends* with a clear **Evaluate · Monitor · Guard** tagline.  

Do you also want me to bake this new README **into your code bundle** and update the dashboard branding (logo/title) to say **AI-Sentinel** instead of “LLM Eval Service”?

