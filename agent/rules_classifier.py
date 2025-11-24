import re
from typing import Dict


class RulesClassifier:
    """Simple heuristic-based classifier for ticket descriptions."""

    CATEGORY_KEYWORDS: Dict[str, tuple[str, ...]] = {
        "Billing": ("invoice", "billing", "payment", "charge", "refund"),
        "Login": ("login", "signin", "password", "reset", "2fa"),
        "Performance": ("slow", "latency", "lag", "timeout", "performance"),
        "Bug": ("error", "bug", "crash", "fail", "exception", "stacktrace"),
        "Question": ("how", "can i", "where", "help", "question"),
    }

    SEVERITY_KEYWORDS: Dict[str, tuple[str, ...]] = {
        "Critical": ("outage", "down", "cannot access", "data loss", "major"),
        "High": ("500", "fails", "failure", "security", "breach", "crash"),
        "Medium": ("degraded", "intermittent", "slow", "issue"),
        "Low": ("typo", "cosmetic", "question", "minor"),
    }

    def classify(self, description: str) -> Dict[str, str]:
        normalized = description.strip()
        summary = self._build_summary(normalized)
        lower_text = normalized.lower()

        category = self._detect_category(lower_text)
        severity = self._detect_severity(lower_text)

        return {"summary": summary, "category": category, "severity": severity}

    def _build_summary(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        first_sentence = sentences[0] if sentences else text
        return first_sentence[:160]

    def _detect_category(self, lower_text: str) -> str:
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in lower_text for keyword in keywords):
                return category
        if "bug" in lower_text or "error" in lower_text:
            return "Bug"
        return "Other"

    def _detect_severity(self, lower_text: str) -> str:
        for severity in ("Critical", "High", "Medium", "Low"):
            keywords = self.SEVERITY_KEYWORDS[severity]
            if any(keyword in lower_text for keyword in keywords):
                return severity
        return "Medium"
