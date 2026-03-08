import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from database import get_db
from routes.auth import get_current_user_id

circles_bp = Blueprint("circles", __name__)


def _is_circle_member(db, circle_owner_id, user_id):
    """Check if user is the circle owner, an existing contact, or has an approved request."""
    if user_id == circle_owner_id:
        return True
    contact = db.execute(
        "SELECT 1 FROM safe_circles WHERE user_id = ? AND contact_id = ?",
        (circle_owner_id, user_id),
    ).fetchone()
    if contact:
        return True
    approved = db.execute(
        "SELECT 1 FROM safe_circle_requests WHERE circle_owner_id = ? AND requester_id = ? AND status = 'approved'",
        (circle_owner_id, user_id),
    ).fetchone()
    return approved is not None


def _is_admin(db, user_id):
    user = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    return user and user["role"] == "Admin"


@circles_bp.route("/api/circles/<circle_owner_id>/members", methods=["GET"])
def get_members(circle_owner_id):
    db = get_db()
    rows = db.execute(
        """SELECT u.id, u.username, u.neighborhood, u.role
           FROM safe_circles sc JOIN users u ON u.id = sc.contact_id
           WHERE sc.user_id = ?""",
        (circle_owner_id,),
    ).fetchall()
    members = [dict(r) for r in rows]

    owner = db.execute(
        "SELECT id, username, neighborhood, role FROM users WHERE id = ?",
        (circle_owner_id,),
    ).fetchone()
    if owner:
        members.insert(0, dict(owner))

    approved = db.execute(
        """SELECT u.id, u.username, u.neighborhood, u.role
           FROM safe_circle_requests r JOIN users u ON u.id = r.requester_id
           WHERE r.circle_owner_id = ? AND r.status = 'approved'""",
        (circle_owner_id,),
    ).fetchall()
    seen = {m["id"] for m in members}
    for r in approved:
        d = dict(r)
        if d["id"] not in seen:
            members.append(d)

    return jsonify(members)


@circles_bp.route("/api/circles/<circle_owner_id>/messages", methods=["GET"])
def get_messages(circle_owner_id):
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    if not _is_circle_member(db, circle_owner_id, caller):
        return jsonify({"error": "Not a member of this circle"}), 403

    rows = db.execute(
        """SELECT m.id, m.content, m.created_at, m.sender_id,
                  u.username AS sender_name
           FROM safe_circle_messages m JOIN users u ON u.id = m.sender_id
           WHERE m.circle_owner_id = ?
           ORDER BY m.created_at ASC""",
        (circle_owner_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@circles_bp.route("/api/circles/<circle_owner_id>/messages", methods=["POST"])
def send_message(circle_owner_id):
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    if not _is_circle_member(db, circle_owner_id, caller):
        return jsonify({"error": "Not a member of this circle"}), 403

    data = request.get_json(silent=True)
    if not data or not data.get("content", "").strip():
        return jsonify({"error": "Message content is required"}), 400

    msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        "INSERT INTO safe_circle_messages (id, circle_owner_id, sender_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (msg_id, circle_owner_id, caller, data["content"].strip()[:2000], now),
    )
    db.commit()

    user = db.execute("SELECT username FROM users WHERE id = ?", (caller,)).fetchone()
    return jsonify({
        "id": msg_id,
        "content": data["content"].strip()[:2000],
        "created_at": now,
        "sender_id": caller,
        "sender_name": user["username"] if user else "Unknown",
    }), 201


@circles_bp.route("/api/circles/<circle_owner_id>/request", methods=["POST"])
def request_join(circle_owner_id):
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    if _is_circle_member(db, circle_owner_id, caller):
        return jsonify({"error": "Already a member"}), 400

    existing = db.execute(
        "SELECT id, status FROM safe_circle_requests WHERE circle_owner_id = ? AND requester_id = ?",
        (circle_owner_id, caller),
    ).fetchone()
    if existing:
        return jsonify({"error": f"Request already {existing['status']}"}), 400

    req_id = f"req_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "INSERT INTO safe_circle_requests (id, circle_owner_id, requester_id, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (req_id, circle_owner_id, caller, now),
    )
    db.commit()
    return jsonify({"id": req_id, "status": "pending"}), 201


@circles_bp.route("/api/circles/<circle_owner_id>/requests", methods=["GET"])
def list_requests(circle_owner_id):
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    if not _is_admin(db, caller):
        return jsonify({"error": "Admin access required"}), 403

    rows = db.execute(
        """SELECT r.id, r.requester_id, r.status, r.created_at,
                  u.username AS requester_name
           FROM safe_circle_requests r JOIN users u ON u.id = r.requester_id
           WHERE r.circle_owner_id = ? AND r.status = 'pending'
           ORDER BY r.created_at ASC""",
        (circle_owner_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@circles_bp.route("/api/circles/<circle_owner_id>/requests/<request_id>", methods=["PATCH"])
def handle_request(circle_owner_id, request_id):
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    if not _is_admin(db, caller):
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    action = data.get("status", "").strip()
    if action not in ("approved", "denied"):
        return jsonify({"error": "Status must be 'approved' or 'denied'"}), 400

    req = db.execute(
        "SELECT * FROM safe_circle_requests WHERE id = ? AND circle_owner_id = ?",
        (request_id, circle_owner_id),
    ).fetchone()
    if not req:
        return jsonify({"error": "Request not found"}), 404

    db.execute("UPDATE safe_circle_requests SET status = ? WHERE id = ?", (action, request_id))

    if action == "approved":
        db.execute(
            "INSERT OR IGNORE INTO safe_circles (user_id, contact_id) VALUES (?, ?)",
            (circle_owner_id, req["requester_id"]),
        )

    db.commit()
    return jsonify({"id": request_id, "status": action})
