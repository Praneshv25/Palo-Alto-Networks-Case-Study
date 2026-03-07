"""Edge cases: AI failures, missing fields, invalid input."""
from unittest.mock import patch


def test_fallback_on_ai_failure(client):
    """When Gemini raises an exception, fallback engine produces a valid report."""
    with patch("services.ai_service._get_client", side_effect=RuntimeError("API down")):
        res = client.post("/api/reports", json={
            "content": "There's a fire in the park near downtown!",
            "category": "local",
            "author_id": "user_002",
        })

    assert res.status_code == 201
    data = res.get_json()
    assert data["is_ai_generated"] is False
    assert data["trust_label"] == "pending_verification"
    assert "fire" in data["title"].lower() or "flagged" in data["title"].lower()
    assert isinstance(data["checklist"], list)
    assert len(data["checklist"]) >= 1


def test_fallback_on_malformed_ai_response(client):
    """When Gemini returns invalid JSON, fallback kicks in."""
    from unittest.mock import MagicMock

    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON at all"

    with patch("services.ai_service._get_client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = mock_response
        res = client.post("/api/reports", json={
            "content": "Scam emails going around asking for bank info",
            "category": "digital",
            "author_id": "user_003",
        })

    assert res.status_code == 201
    data = res.get_json()
    assert data["is_ai_generated"] is False
    assert data["trust_label"] == "pending_verification"


def test_empty_content_rejected(client):
    """POST with empty content returns 400."""
    res = client.post("/api/reports", json={
        "content": "",
        "category": "local",
        "author_id": "user_001",
    })
    assert res.status_code == 400
    assert "content" in res.get_json()["error"].lower()


def test_missing_content_rejected(client):
    """POST with no content field returns 400."""
    res = client.post("/api/reports", json={
        "category": "local",
        "author_id": "user_001",
    })
    assert res.status_code == 400


def test_invalid_category_rejected(client):
    """POST with invalid category returns 400."""
    res = client.post("/api/reports", json={
        "content": "Something happened",
        "category": "invalid_category",
        "author_id": "user_001",
    })
    assert res.status_code == 400
    assert "category" in res.get_json()["error"].lower()


def test_invalid_user_rejected(client):
    """POST with non-existent user returns 400."""
    res = client.post("/api/reports", json={
        "content": "Something happened",
        "category": "local",
        "author_id": "nonexistent_user",
    })
    assert res.status_code == 400


def test_patch_nonexistent_report(client):
    """PATCH a report that doesn't exist returns 404."""
    res = client.patch("/api/reports/nonexistent_id", json={
        "status": "Resolved",
    })
    assert res.status_code == 404


def test_patch_invalid_status(client):
    """PATCH with an invalid status returns 400."""
    res = client.get("/api/reports")
    reports = res.get_json()
    if reports:
        report_id = reports[0]["id"]
        res = client.patch(f"/api/reports/{report_id}", json={
            "status": "InvalidStatus",
        })
        assert res.status_code == 400
