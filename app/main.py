import logging

from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.schemas import HealthResponse, TriageRequest, TriageResponse
from agent.groq_client import GroqAssistant
from agent.kb_search import KnowledgeBaseSearch
from agent.triage_agent import TriageAgent

logger = logging.getLogger("support_triage.app")


def get_agent(settings: Settings = Depends(get_settings)) -> TriageAgent:
    """Construct and cache the triage agent."""
    if not hasattr(get_agent, "_agent"):
        logger.info("Bootstrapping triage agent", extra={"provider": settings.llm_provider})
        llm_client = GroqAssistant(
            provider=settings.llm_provider,
            api_key=settings.groq_api_key,
            match_threshold=settings.kb_similarity_threshold,
        )
        kb = KnowledgeBaseSearch(kb_path=settings.kb_path)
        get_agent._agent = TriageAgent(
            llm_client=llm_client,
            kb_search=kb,
            match_threshold=settings.kb_similarity_threshold,
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
