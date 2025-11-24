from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_triage_endpoint_success():
    payload = {"description": "Checkout keeps failing with 500 error when paying by card"}
    response = client.post("/triage", json=payload)

    assert response.status_code == 200
    data = response.json()
    for key in {"summary", "category", "severity", "related_issues", "known_issue", "suggested_next_step"}:
        assert key in data
    assert isinstance(data["related_issues"], list)


def test_triage_endpoint_validation_error():
    response = client.post("/triage", json={"description": "too short"})
    assert response.status_code == 422
