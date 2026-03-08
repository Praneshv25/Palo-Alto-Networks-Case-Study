import json
import re
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from database import get_db
from services.ai_service import filter_with_ai
from services.fallback import analyze_with_fallback

reports_bp = Blueprint("reports", __name__)

MAX_CONTENT_LENGTH = 5000


def _sanitize(text):
    """Strip HTML tags and limit length."""
    cleaned = re.sub(r'<[^>]+>', '', str(text))
    return cleaned[:MAX_CONTENT_LENGTH]


def _row_to_dict(row):
    d = dict(row)
    d["checklist"] = json.loads(d["checklist"])
    d["is_ai_generated"] = bool(d["is_ai_generated"])
    return d


@reports_bp.route("/api/reports", methods=["POST"])
def create_report():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    content = data.get("content", "").strip()
    category_input = data.get("category", "").strip().lower()
    author_id = data.get("author_id", "").strip()

    if not content:
        return jsonify({"error": "Field 'content' is required and cannot be empty"}), 400
    if category_input not in ("local", "digital"):
        return jsonify({"error": "Field 'category' must be 'local' or 'digital'"}), 400
    if not author_id:
        return jsonify({"error": "Field 'author_id' is required"}), 400

    content = _sanitize(content)
    db = get_db()

    user = db.execute("SELECT id FROM users WHERE id = ?", (author_id,)).fetchone()
    if not user:
        return jsonify({"error": f"User '{author_id}' not found"}), 400

    post_id = f"post_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        "INSERT INTO raw_posts (id, author_id, content, timestamp, source_type) VALUES (?, ?, ?, ?, ?)",
        (post_id, author_id, content, now, "Manual_Entry"),
    )
    db.commit()

    try:
        ai_result = filter_with_ai(content)
        is_ai_generated = 1
        trust_label = "ai_generated"
    except Exception:
        ai_result = analyze_with_fallback(content)
        is_ai_generated = 0
        trust_label = "pending_verification"

    if category_input == "local":
        ai_result["category"] = "Local_Physical"
    else:
        ai_result["category"] = "Digital_Security"

    report_id = f"rep_{uuid.uuid4().hex[:8]}"
    checklist_json = json.dumps(ai_result["checklist"])

    db.execute(
        """INSERT INTO safety_reports
           (id, parent_post_id, category, severity, title, summary, checklist,
            status, location_radius, is_ai_generated, trust_label, upvotes, downvotes,
            resolution_note, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', 500, ?, ?, 0, 0, NULL, ?)""",
        (report_id, post_id, ai_result["category"], ai_result["severity"],
         ai_result["title"], ai_result["summary"], checklist_json,
         is_ai_generated, trust_label, now),
    )
    db.commit()

    report = db.execute("SELECT * FROM safety_reports WHERE id = ?", (report_id,)).fetchone()
    return jsonify(_row_to_dict(report)), 201


@reports_bp.route("/api/reports", methods=["GET"])
def get_reports():
    db = get_db()
    query = "SELECT * FROM safety_reports WHERE 1=1"
    params = []

    category = request.args.get("category", "").strip().lower()
    if category == "local":
        query += " AND category = ?"
        params.append("Local_Physical")
    elif category == "digital":
        query += " AND category = ?"
        params.append("Digital_Security")

    status = request.args.get("status", "").strip().lower()
    if status == "active":
        query += " AND status = ?"
        params.append("Active")
    elif status == "resolved":
        query += " AND status = ?"
        params.append("Resolved")

    search = request.args.get("search", "").strip()
    if search:
        query += " AND (title LIKE ? OR summary LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    severity = request.args.get("severity", "").strip()
    if severity in ("Low", "Medium", "High"):
        query += " AND severity = ?"
        params.append(severity)

    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()
    return jsonify([_row_to_dict(r) for r in rows])


@reports_bp.route("/api/reports/<report_id>", methods=["PATCH"])
def update_report(report_id):
    db = get_db()
    report = db.execute("SELECT * FROM safety_reports WHERE id = ?", (report_id,)).fetchone()
    if not report:
        return jsonify({"error": "Report not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    new_status = data.get("status", "").strip()
    if new_status not in ("Active", "Resolved"):
        return jsonify({"error": "Field 'status' must be 'Active' or 'Resolved'"}), 400

    resolution_note = _sanitize(data.get("resolution_note", "") or "")

    db.execute(
        "UPDATE safety_reports SET status = ?, resolution_note = ? WHERE id = ?",
        (new_status, resolution_note if resolution_note else None, report_id),
    )
    db.commit()

    updated = db.execute("SELECT * FROM safety_reports WHERE id = ?", (report_id,)).fetchone()
    return jsonify(_row_to_dict(updated))
