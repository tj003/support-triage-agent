# support-triage-agent

This is my “get-it-done” support triage stack: FastAPI on the edge, a Streamlit scratchpad for humans, a tuned keyword KB search, and optional Groq-powered judgement calls when I want higher fidelity.

---

## Getting Started

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

---

## API Usage

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"description":"Checkout keeps failing with 500 error when paying"}'
```

Health check: `GET /health`

---

## Why Groq?

- Lowest-latency OSS LLaMA serving I’ve found for this use case
- Structured JSON output keeps the pipeline deterministic
- Works great as “assist mode” for High/Critical tickets while the rules handle the long tail

### Enabling Groq Mode

```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=sk_your_key_here
```

or drop the values into `.env` (handy for Streamlit).

Under the hood:

1. Classification prompt enforces `{"summary","category","severity"}` JSON
2. Next-action prompt asks for 1–2 sentences prioritizing revenue + uptime
3. If Groq errors or times out, we drop back to the deterministic heuristics

---

## Error Handling & Resiliency

- Every external hop (Groq + KB I/O) is wrapped with logging + safe fallbacks
- Rule-based summary/category/severity remains available even without an API key
- KB search adds a symptom boost so exact strings like “500 error” win over fuzzy matches
- Configurable `KB_SIMILARITY_THRESHOLD` keeps “known issue” tagging predictable

---

## Running Tests

```bash
python -m pytest
```

---

## Docker

```bash
docker build -t support-triage-agent .
docker run -p 8000:8000 support-triage-agent
```

---

## Changelog

- Groq-backed classification + guidance with clean fallbacks
- Refined KB scorer with symptom bonus + better logging
- Streamlit + FastAPI share the same triage service wiring
- Settings promote env-based overrides (paths, thresholds, providers)

### Roadmap

- Embedding-based KB search (hybrid semantic + keyword)
- Conversation memory for Streamlit to compare revisions
- Alert hooks (Slack/webhooks) for Critical escalations

---

## Production Considerations

- Deploy via container platform of choice (ECS, GKE, Cloud Run, etc.)
- Ship logs/metrics to your observability stack; the logger tags provider + context
- Terminate TLS + rate-limit at the ingress/gateway layer
- Keep KB JSON in object storage or a managed doc store if it grows beyond local usage
