import logging
from typing import Dict, List

from agent.groq_client import GroqAssistant
from agent.kb_search import KnowledgeBaseSearch


class TriageAgent:
    """Co-ordinates classification, KB search, and next-step selection."""

    def __init__(
        self,
        llm_client: GroqAssistant,
        kb_search: KnowledgeBaseSearch,
        match_threshold: float = 0.35,
        max_related: int = 3,
    ) -> None:
        self.llm_client = llm_client
        self.kb_search = kb_search
        self.match_threshold = match_threshold
        self.max_related = max_related
        self.logger = logging.getLogger(__name__)

    def triage(self, description: str) -> Dict[str, object]:
        """Primary entry point used by both FastAPI and Streamlit."""
        clean_text = description.strip()
        if len(clean_text) < 10:
            raise ValueError("Description must be at least 10 characters long")

        self.logger.debug("Triage started", extra={"chars": len(clean_text)})

        profile = self.llm_client.classify_ticket(clean_text)
        kb_hits = self.kb_search.lookup(clean_text, limit=self.max_related)
        known_issue = bool(kb_hits) and kb_hits[0]["similarity"] >= self.match_threshold

        if self._should_request_llm(profile["severity"]):
            next_step = self.llm_client.suggest_next_action(
                clean_text, profile["category"], profile["severity"], kb_hits
            )
        else:
            next_step = self._fallback_action(known_issue, profile["severity"])

        return {
            **profile,
            "related_issues": kb_hits,
            "known_issue": known_issue,
            "suggested_next_step": next_step,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _should_request_llm(self, severity: str) -> bool:
        """LLM handles High/Critical tickets or whenever Groq mode is enabled."""
        return self.llm_client.provider == "groq" or severity in {"High", "Critical"}

    def _fallback_action(self, known_issue: bool, severity: str) -> str:
        """Readable local logic matching legacy behavior."""
        severe = severity in {"High", "Critical"}
        if known_issue and severe:
            return "Attach KB article & escalate to backend"
        if known_issue:
            return "Attach KB article & respond to user"
        if severe:
            return "Escalate to backend team"
        return "Ask for more logs & assign to support"
