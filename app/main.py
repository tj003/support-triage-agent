from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.schemas import HealthResponse, TriageRequest, TriageResponse
from agent.kb_search import KBSearch
from agent.rules_classifier import RulesClassifier
from agent.triage_agent import TriageAgent


def get_agent(settings: Settings = Depends(get_settings)) -> TriageAgent:
    """Construct and cache the triage agent."""
    if not hasattr(get_agent, "_agent"):
        rules = RulesClassifier()
        kb = KBSearch(kb_path=settings.kb_path)
        get_agent._agent = TriageAgent(
            rules_classifier=rules,
            kb_search=kb,
            similarity_threshold=settings.similarity_threshold,
            max_related=settings.max_related_results,
        )
    return get_agent._agent  # type: ignore[attr-defined]


app = FastAPI(title="Support Triage Agent")


@app.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(environment=settings.environment)


@app.post("/triage", response_model=TriageResponse)
def triage_ticket(
    request: TriageRequest, agent: TriageAgent = Depends(get_agent)
) -> TriageResponse:
    try:
        result = agent.triage(request.description)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TriageResponse(**result)
