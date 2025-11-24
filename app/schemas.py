from typing import List
from pydantic import BaseModel, Field, validator


class TriageRequest(BaseModel):
    description: str = Field(..., min_length=10)

    @validator("description")
    def description_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("Description must be at least 10 characters long")
        return cleaned


class RelatedIssue(BaseModel):
    id: str
    title: str
    similarity: float
    recommended_action: str


class TriageResponse(BaseModel):
    summary: str
    category: str
    severity: str
    related_issues: List[RelatedIssue]
    known_issue: bool
    suggested_next_step: str


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
