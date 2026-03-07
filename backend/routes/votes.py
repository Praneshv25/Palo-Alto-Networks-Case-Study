import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from database import get_db
from services.trust import compute_trust_label

votes_bp = Blueprint("votes", __name__)


@votes_bp.route("/api/reports/<report_id>/vote", methods=["POST"])
def cast_vote(report_id):
    db = get_db()

    report = db.execute("SELECT id FROM safety_reports WHERE id = ?", (report_id,)).fetchone()
    if not report:
        return jsonify({"error": "Report not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    user_id = data.get("user_id", "").strip()
    vote_type = data.get("vote_type", "").strip()

    if not user_id:
        return jsonify({"error": "Field 'user_id' is required"}), 400
    if vote_type not in ("up", "down"):
        return jsonify({"error": "Field 'vote_type' must be 'up' or 'down'"}), 400

    user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": f"User '{user_id}' not found"}), 400

    existing = db.execute(
        "SELECT id, vote_type FROM votes WHERE report_id = ? AND user_id = ?",
        (report_id, user_id),
    ).fetchone()

    user_vote = None

    if existing:
        if existing["vote_type"] == vote_type:
            # Toggle off — remove the vote
            db.execute("DELETE FROM votes WHERE id = ?", (existing["id"],))
            col = "upvotes" if vote_type == "up" else "downvotes"
            db.execute(f"UPDATE safety_reports SET {col} = {col} - 1 WHERE id = ?", (report_id,))
            user_vote = None
        else:
            # Switch vote direction
            db.execute("UPDATE votes SET vote_type = ? WHERE id = ?", (vote_type, existing["id"]))
            if vote_type == "up":
                db.execute("UPDATE safety_reports SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?", (report_id,))
            else:
                db.execute("UPDATE safety_reports SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?", (report_id,))
            user_vote = vote_type
    else:
        # New vote
        vote_id = f"vote_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO votes (id, report_id, user_id, vote_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (vote_id, report_id, user_id, vote_type, now),
        )
        col = "upvotes" if vote_type == "up" else "downvotes"
        db.execute(f"UPDATE safety_reports SET {col} = {col} + 1 WHERE id = ?", (report_id,))
        user_vote = vote_type

    db.commit()

    trust_label = compute_trust_label(db, report_id)

    updated = db.execute(
        "SELECT upvotes, downvotes, trust_label FROM safety_reports WHERE id = ?",
        (report_id,),
    ).fetchone()

    return jsonify({
        "upvotes": updated["upvotes"],
        "downvotes": updated["downvotes"],
        "trust_label": updated["trust_label"],
        "user_vote": user_vote,
    })
