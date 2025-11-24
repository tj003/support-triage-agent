from typing import Dict, List

from agent.kb_search import KBSearch
from agent.rules_classifier import RulesClassifier


class TriageAgent:
    def __init__(
        self,
        rules_classifier: RulesClassifier,
        kb_search: KBSearch,
        similarity_threshold: float = 0.35,
        max_related: int = 3,
    ) -> None:
        self.rules_classifier = rules_classifier
        self.kb_search = kb_search
        self.similarity_threshold = similarity_threshold
        self.max_related = max_related

    def triage(self, description: str) -> Dict[str, object]:
        if not description or len(description.strip()) < 10:
            raise ValueError("Description must be at least 10 characters long")

        classification = self.rules_classifier.classify(description)
        related = self.kb_search.search(description, max_results=self.max_related)
        known_issue = bool(related) and related[0]["similarity"] >= self.similarity_threshold
        suggested_next_step = self._determine_next_step(known_issue, classification["severity"])

        return {
            **classification,
            "related_issues": related,
            "known_issue": known_issue,
            "suggested_next_step": suggested_next_step,
        }

    def _determine_next_step(self, known_issue: bool, severity: str) -> str:
        severe = severity in {"High", "Critical"}
        if known_issue:
            if severe:
                return "Attach KB article & escalate to backend"
            return "Attach KB article & respond to user"
        if severe:
            return "Escalate to backend team"
        return "Ask for more logs & assign to support"
