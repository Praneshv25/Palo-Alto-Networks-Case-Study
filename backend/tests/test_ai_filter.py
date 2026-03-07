"""Happy path: noisy post -> calm AI-filtered report."""
import json
from unittest.mock import patch, MagicMock


MOCK_AI_RESPONSE = {
    "title": "Vegetation Fire: Elm Street Area",
    "summary": "A fire has been reported on Elm Street. Emergency services are en route.",
    "severity": "High",
    "category": "Local_Physical",
    "checklist": [
        "Avoid Elm Street and surrounding blocks.",
        "Close windows if you smell smoke.",
        "Check official city alerts for updates.",
    ],
}


def test_create_report_with_ai_success(client):
    """POST /api/reports produces a calm, de-escalated report via mocked Gemini."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(MOCK_AI_RESPONSE)

    with patch("services.ai_service._get_client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = mock_response

        res = client.post("/api/reports", json={
            "content": "OMG THERE IS A CRAZY FIRE ON ELM STREET EVERYONE IS GOING TO DIE!!!",
            "category": "local",
            "author_id": "user_002",
        })

    assert res.status_code == 201
    data = res.get_json()

    assert data["title"] == "Vegetation Fire: Elm Street Area"
    assert "calm" not in data["summary"].lower() or "fire" in data["summary"].lower()
    assert data["severity"] == "High"
    assert data["is_ai_generated"] is True
    assert data["trust_label"] == "ai_generated"
    assert isinstance(data["checklist"], list)
    assert len(data["checklist"]) == 3
    assert data["status"] == "Active"
    assert data["upvotes"] == 0
    assert data["downvotes"] == 0


def test_created_report_appears_in_feed(client):
    """A created report should show up in GET /api/reports."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(MOCK_AI_RESPONSE)

    with patch("services.ai_service._get_client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = mock_response
        client.post("/api/reports", json={
            "content": "Fire on Elm Street!",
            "category": "local",
            "author_id": "user_001",
        })

    res = client.get("/api/reports?category=local")
    data = res.get_json()

    titles = [r["title"] for r in data]
    assert "Vegetation Fire: Elm Street Area" in titles
