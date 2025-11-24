# support-triage-agent

Local-only Support Ticket Triage Agent that combines FastAPI, rule-based classification, and a lightweight knowledge-base search to suggest next actions for support engineers.

## Getting Started

```bash
python -m venv .venv
. .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

## Usage

POST descriptions to `/triage`:

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"description":"I see 500 error when paying"}'
```

Health check: `GET /health`.

## Running Tests

```bash
pytest
```

## Docker

```bash
docker build -t support-triage-agent .
docker run -p 8000:8000 support-triage-agent
```

## Production Considerations

- Deploy the container via preferred cloud provider (AWS ECS/EKS, GCP GKE/Cloud Run, Azure Container Apps).
- Enable structured logging and ship logs/metrics to your observability stack (CloudWatch, Stackdriver, Azure Monitor, etc.).
- Use environment-based configuration for KB path, thresholds, and secrets through `Settings`.
- Apply rate limiting and authentication at the API gateway or ingress to block abuse.
