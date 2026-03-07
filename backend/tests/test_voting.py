"""Voting: trust badge transitions, toggle, switch."""
import json
from unittest.mock import patch, MagicMock


MOCK_AI = {
    "title": "Test Report",
    "summary": "A test incident was reported.",
    "severity": "Medium",
    "category": "Local_Physical",
    "checklist": ["Step 1.", "Step 2.", "Step 3."],
}


def _create_report(client):
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(MOCK_AI)
    with patch("services.ai_service._get_client") as mc:
        mc.return_value.models.generate_content.return_value = mock_resp
        res = client.post("/api/reports", json={
            "content": "Something happened nearby",
            "category": "local",
            "author_id": "user_001",
        })
    return res.get_json()["id"]


def test_upvote_increments_count(client):
    rid = _create_report(client)
    res = client.post(f"/api/reports/{rid}/vote", json={
        "user_id": "user_002",
        "vote_type": "up",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["upvotes"] == 1
    assert data["downvotes"] == 0
    assert data["user_vote"] == "up"


def test_toggle_vote_removes_it(client):
    rid = _create_report(client)
    client.post(f"/api/reports/{rid}/vote", json={"user_id": "user_002", "vote_type": "up"})
    res = client.post(f"/api/reports/{rid}/vote", json={"user_id": "user_002", "vote_type": "up"})
    data = res.get_json()
    assert data["upvotes"] == 0
    assert data["user_vote"] is None


def test_switch_vote_direction(client):
    rid = _create_report(client)
    client.post(f"/api/reports/{rid}/vote", json={"user_id": "user_002", "vote_type": "up"})
    res = client.post(f"/api/reports/{rid}/vote", json={"user_id": "user_002", "vote_type": "down"})
    data = res.get_json()
    assert data["upvotes"] == 0
    assert data["downvotes"] == 1
    assert data["user_vote"] == "down"


def test_community_verified_threshold(client):
    """3+ upvotes with ratio > 2x downvotes -> community_verified."""
    rid = _create_report(client)
    for uid in ["user_001", "user_002", "user_003"]:
        client.post(f"/api/reports/{rid}/vote", json={"user_id": uid, "vote_type": "up"})

    res = client.get("/api/reports")
    report = next(r for r in res.get_json() if r["id"] == rid)
    assert report["trust_label"] == "community_verified"
    assert report["upvotes"] == 3


def test_flagged_threshold(client):
    """3+ downvotes exceeding upvotes -> flagged."""
    rid = _create_report(client)
    for uid in ["user_002", "user_003", "user_004"]:
        client.post(f"/api/reports/{rid}/vote", json={"user_id": uid, "vote_type": "down"})

    res = client.get("/api/reports")
    report = next(r for r in res.get_json() if r["id"] == rid)
    assert report["trust_label"] == "flagged"
    assert report["downvotes"] == 3


def test_invalid_vote_type_rejected(client):
    rid = _create_report(client)
    res = client.post(f"/api/reports/{rid}/vote", json={
        "user_id": "user_002",
        "vote_type": "sideways",
    })
    assert res.status_code == 400


def test_vote_on_nonexistent_report(client):
    res = client.post("/api/reports/fake_report/vote", json={
        "user_id": "user_001",
        "vote_type": "up",
    })
    assert res.status_code == 404
