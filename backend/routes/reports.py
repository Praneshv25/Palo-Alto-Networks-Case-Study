import json
import math
import re
import uuid
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from database import get_db
from services.ai_service import filter_with_ai, check_and_aggregate
from services.fallback import analyze_with_fallback, jaccard_similarity, fallback_merge

reports_bp = Blueprint("reports", __name__)

MAX_CONTENT_LENGTH = 5000
AGGREGATION_WINDOW_MINUTES = 60


def _haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in kilometres between two (lat, lng) points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _find_recent_active_reports(db, category, minutes=AGGREGATION_WINDOW_MINUTES):
    """Return up to 5 active reports in the same category from the last N minutes."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    return db.execute(
        """SELECT * FROM safety_reports
           WHERE category = ? AND status = 'Active' AND created_at > ?
           ORDER BY created_at DESC LIMIT 5""",
        (category, cutoff),
    ).fetchall()


def _sanitize(text):
    """Strip HTML tags and limit length."""
    cleaned = re.sub(r'<[^>]+>', '', str(text))
    return cleaned[:MAX_CONTENT_LENGTH]


def _row_to_dict(row):
    d = dict(row)
    d["checklist"] = json.loads(d["checklist"])
    d["is_ai_generated"] = bool(d["is_ai_generated"])
    d.setdefault("source_count", 1)
    d["lat"] = float(d["lat"]) if d.get("lat") is not None else None
    d["lng"] = float(d["lng"]) if d.get("lng") is not None else None
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

    try:
        report_lat = float(data["lat"]) if data.get("lat") is not None else None
        report_lng = float(data["lng"]) if data.get("lng") is not None else None
    except (TypeError, ValueError):
        report_lat, report_lng = None, None

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
    except Exception as e:
        print(f"[AI] Gemini failed ({type(e).__name__}): {e}")
        ai_result = analyze_with_fallback(content)
        is_ai_generated = 0
        trust_label = "pending_verification"

    if category_input == "local":
        ai_result["category"] = "Local_Physical"
    else:
        ai_result["category"] = "Digital_Security"

    # --- Aggregation: check if any recent report covers the same incident ---
    candidates = _find_recent_active_reports(db, ai_result["category"])
    for candidate in candidates:
        merged = None

        if is_ai_generated:
            # Gemini is available: ask it to judge similarity and produce merged content
            try:
                agg = check_and_aggregate(
                    candidate["title"],
                    candidate["summary"],
                    content,
                )
                if agg["same_incident"]:
                    merged = {
                        "title": agg["title"],
                        "summary": agg["summary"],
                        "severity": agg["severity"],
                        "checklist": agg["checklist"],
                    }
            except Exception as e:
                print(f"[AI] Aggregation check failed ({type(e).__name__}): {e}")
                # Fall through to rule-based similarity below
        
        if merged is None:
            # Gemini unavailable or failed: use word-overlap similarity
            existing_text = candidate["title"] + " " + candidate["summary"]
            sim = jaccard_similarity(existing_text, content)
            print(f"[AGG] Fallback similarity with {candidate['id']}: {sim:.2f}")
            if sim >= 0.25:
                merged = fallback_merge(dict(candidate), content)

        if merged is not None:
            print(f"[AGG] Merging into existing report {candidate['id']}")
            db.execute(
                """UPDATE safety_reports
                   SET title = ?, summary = ?, severity = ?,
                       checklist = ?, source_count = source_count + 1
                   WHERE id = ?""",
                (
                    merged["title"],
                    merged["summary"],
                    merged["severity"],
                    json.dumps(merged["checklist"]),
                    candidate["id"],
                ),
            )
            db.commit()
            updated = db.execute(
                "SELECT * FROM safety_reports WHERE id = ?", (candidate["id"],)
            ).fetchone()
            return jsonify(_row_to_dict(updated)), 200
    # -----------------------------------------------------------------------

    report_id = f"rep_{uuid.uuid4().hex[:8]}"
    checklist_json = json.dumps(ai_result["checklist"])

    db.execute(
        """INSERT INTO safety_reports
           (id, parent_post_id, category, severity, title, summary, checklist,
            status, location_radius, is_ai_generated, trust_label, upvotes, downvotes,
            resolution_note, created_at, lat, lng)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', 500, ?, ?, 0, 0, NULL, ?, ?, ?)""",
        (report_id, post_id, ai_result["category"], ai_result["severity"],
         ai_result["title"], ai_result["summary"], checklist_json,
         is_ai_generated, trust_label, now, report_lat, report_lng),
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

    # Optional proximity filter — applied in Python after fetch
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
        radius_km = float(request.args.get("radius_km", 10))
    except (TypeError, ValueError):
        user_lat = user_lng = None

    result = []
    for r in rows:
        d = _row_to_dict(r)
        if user_lat is not None and d["lat"] is not None and d["lng"] is not None:
            km = _haversine_km(user_lat, user_lng, d["lat"], d["lng"])
            if km > radius_km:
                continue
        result.append(d)

    return jsonify(result)


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
