import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from database import get_db
from routes.auth import get_current_user_id

circles_bp = Blueprint("circles", __name__)


def _is_circle_member(db, circle_owner_id, user_id):
    if user_id == circle_owner_id:
        return True
    contact = db.execute(
        "SELECT 1 FROM safe_circles WHERE user_id = ? AND contact_id = ?",
        (circle_owner_id, user_id),
    ).fetchone()
    return contact is not None


@circles_bp.route("/api/circles/mine", methods=["GET"])
def get_my_circle():
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    rows = db.execute(
        """SELECT u.id, u.username, u.neighborhood, u.role
           FROM safe_circles sc JOIN users u ON u.id = sc.contact_id
           WHERE sc.user_id = ?""",
        (caller,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@circles_bp.route("/api/circles/memberships", methods=["GET"])
def get_memberships():
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    rows = db.execute(
        """SELECT u.id AS owner_id, u.username AS owner_name, u.neighborhood AS owner_neighborhood
           FROM safe_circles sc JOIN users u ON u.id = sc.user_id
           WHERE sc.contact_id = ?""",
        (caller,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@circles_bp.route("/api/circles/members", methods=["POST"])
def add_member():
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True)
    if not data or not data.get("contact_id", "").strip():
        return jsonify({"error": "Field 'contact_id' is required"}), 400

    contact_id = data["contact_id"].strip()
    if contact_id == caller:
        return jsonify({"error": "Cannot add yourself"}), 400

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE id = ?", (contact_id,)).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    existing = db.execute(
        "SELECT 1 FROM safe_circles WHERE user_id = ? AND contact_id = ?",
        (caller, contact_id),
    ).fetchone()
    if existing:
        return jsonify({"error": "Already in your circle"}), 400

    db.execute(
        "INSERT INTO safe_circles (user_id, contact_id) VALUES (?, ?)",
        (caller, contact_id),
    )
    db.commit()

    added = db.execute(
        "SELECT id, username, neighborhood, role FROM users WHERE id = ?",
        (contact_id,),
    ).fetchone()
    return jsonify(dict(added)), 201


@circles_bp.route("/api/circles/members/<contact_id>", methods=["DELETE"])
def remove_member(contact_id):
    caller = get_current_user_id()
    if not caller:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    db.execute(
        "DELETE FROM safe_circles WHERE user_id = ? AND contact_id = ?",
        (caller, contact_id),
    )
    db.commit()
    return jsonify({"ok": True})


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
