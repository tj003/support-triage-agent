from agent.kb_search import KBSearch
from agent.triage_agent import TriageAgent


class StubRules:
    def __init__(self, summary: str, category: str, severity: str) -> None:
        self.summary = summary
        self.category = category
        self.severity = severity

    def classify(self, description: str):
        return {
            "summary": self.summary,
            "category": self.category,
            "severity": self.severity,
        }


def build_agent(severity: str, kb_entries, threshold: float = 0.35) -> TriageAgent:
    rules = StubRules("stub summary", "Bug", severity)
    kb = KBSearch(entries=kb_entries)
    return TriageAgent(rules, kb, similarity_threshold=threshold)


def test_known_issue_path():
    kb_entries = [
        {
            "id": "KB1",
            "title": "Checkout failure 500",
            "category": "Bug",
            "symptoms": ["checkout", "500", "card"],
            "recommended_action": "Escalate to payments",
        }
    ]
    agent = build_agent("High", kb_entries, threshold=0.2)

    result = agent.triage("Checkout keeps failing with 500 error on card payments")

    assert result["known_issue"] is True
    assert result["suggested_next_step"] == "Attach KB article & escalate to backend"
    assert result["related_issues"][0]["id"] == "KB1"


def test_unknown_issue_non_severe_path():
    kb_entries = [
        {
            "id": "KB2",
            "title": "Login email missing",
            "category": "Login",
            "symptoms": ["login", "email"],
            "recommended_action": "Resend email",
        }
    ]
    agent = build_agent("Low", kb_entries)

    result = agent.triage("Profile avatar looks pixelated on dashboard settings")

    assert result["known_issue"] is False
    assert result["suggested_next_step"] == "Ask for more logs & assign to support"


def test_unknown_issue_severe_escalation():
    kb_entries = []
    agent = build_agent("Critical", kb_entries)

    result = agent.triage("Major outage preventing all logins")

    assert result["known_issue"] is False
    assert result["suggested_next_step"] == "Escalate to backend team"
