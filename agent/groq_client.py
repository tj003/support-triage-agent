import json
import logging
from typing import Dict, List, Optional

from agent.rules_classifier import RulesClassifier

_ALLOWED_CATEGORIES = {"Billing", "Login", "Performance", "Bug", "Question", "Other"}
_ALLOWED_SEVERITIES = {"Low", "Medium", "High", "Critical"}
_CLASSIFICATION_PROMPT = (
    "You are a support operations classifier. Extract structured JSON exactly as:\n"
    '{"summary": "...", "category": "...", "severity": "..."}\n'
    "Valid category: Billing | Login | Performance | Bug | Question | Other\n"
    "Valid severity: Low | Medium | High | Critical\n"
    "Make sure your response is only valid JSON with no extra words."
)
_NEXT_ACTION_PROMPT = (
    "You are a senior support engineer. In 1-2 short actionable sentences, advise what the support agent "
    "should do next based on issue severity, category and KB context. Focus on revenue, service continuity, "
    "and user impact."
)


class GroqAssistant:
    """Wrapper that can talk to Groq or fall back to local heuristics."""

    def __init__(
        self,
        provider: str = "mock",
        api_key: Optional[str] = None,
        match_threshold: float = 0.35,
    ) -> None:
        self.provider = (provider or "mock").lower()
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.rules_fallback = RulesClassifier()
        self._client = None
        self._model = "llama3-8b-8192"
        self.match_threshold = match_threshold

        if self.provider == "groq":
            if not api_key:
                raise ValueError("GROQ_API_KEY must be set when LLM_PROVIDER=groq")
            try:
                from groq import Groq
            except ImportError as exc:  # pragma: no cover - import guard
                raise ImportError("groq package is required for Groq mode") from exc
            self._client = Groq(api_key=api_key)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def classify_ticket(self, description: str) -> Dict[str, str]:
        """Return summary/category/severity for a support ticket."""
        text = description.strip()
        if not text:
            raise ValueError("Description cannot be empty")

        if self.provider != "groq":
            return self.rules_fallback.classify(text)

        try:
            completion = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=self._model,
                messages=[
                    {"role": "system", "content": _CLASSIFICATION_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            payload = completion.choices[0].message.content
            parsed = json.loads(payload)
        except Exception as exc:  # noqa: BLE001 - log + fallback is intentional
            self.logger.warning("Groq classification failed; falling back to heuristics: %s", exc)
            return self.rules_fallback.classify(text)

        summary = self._trim_summary(parsed.get("summary") or text)
        category = self._normalize_category(parsed.get("category"))
        severity = self._normalize_severity(parsed.get("severity"))
        return {"summary": summary, "category": category, "severity": severity}

    def suggest_next_action(
        self,
        description: str,
        category: str,
        severity: str,
        related_issues: List[Dict[str, object]],
    ) -> str:
        """Return an actionable next step using Groq when available."""
        if self.provider != "groq":
            return self._rule_based_action(related_issues, severity)

        kb_context = self._render_kb_context(related_issues)
        try:
            completion = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=self._model,
                messages=[
                    {"role": "system", "content": _NEXT_ACTION_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Description: {description}\n"
                            f"Category: {category}\n"
                            f"Severity: {severity}\n"
                            f"{kb_context}\n"
                            "Respond with 1-2 short actionable sentences."
                        ),
                    },
                ],
                temperature=0.5,
                max_tokens=150,
            )
            content = completion.choices[0].message.content.strip()
            return content.strip('"').strip("'").strip()[:200]
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Groq next-action failed; reverting to rules: %s", exc)
            return self._rule_based_action(related_issues, severity)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _rule_based_action(self, related_issues: List[Dict[str, object]], severity: str) -> str:
        """Simple deterministic fallback for suggested_next_step."""
        has_match = bool(related_issues) and related_issues[0].get("similarity", 0) >= self.match_threshold
        severe = severity in {"High", "Critical"}
        if has_match:
            return "Attach KB article & escalate to backend" if severe else "Attach KB article & respond to user"
        return "Escalate to backend team" if severe else "Ask for more logs & assign to support"

    def _normalize_category(self, category: Optional[str]) -> str:
        if not category:
            return "Other"
        cleaned = category.strip()
        if cleaned in _ALLOWED_CATEGORIES:
            return cleaned
        for candidate in _ALLOWED_CATEGORIES:
            if cleaned.lower() == candidate.lower():
                return candidate
        return "Other"

    def _normalize_severity(self, severity: Optional[str]) -> str:
        if not severity:
            return "Medium"
        cleaned = severity.strip()
        if cleaned in _ALLOWED_SEVERITIES:
            return cleaned
        for candidate in _ALLOWED_SEVERITIES:
            if cleaned.lower() == candidate.lower():
                return candidate
        return "Medium"

    def _trim_summary(self, summary: str) -> str:
        return summary.strip()[:160]

    def _render_kb_context(self, related_issues: List[Dict[str, object]]) -> str:
        if not related_issues:
            return "No KB context found."
        lines = ["Related KB matches:"]
        for issue in related_issues[:3]:
            title = issue.get("title", "(untitled)")
            action = issue.get("recommended_action", "")
            score = issue.get("similarity", 0)
            lines.append(f"- {title} (score {score}): {action}")
        return "\n".join(lines)
