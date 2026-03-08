import uuid
from flask import Blueprint, request, jsonify
from database import get_db

auth_bp = Blueprint("auth", __name__)

CREDENTIALS = {
    "maria": {"password": "pass123", "user_id": "user_001"},
    "jake": {"password": "pass456", "user_id": "user_002"},
    "aisha": {"password": "pass789", "user_id": "user_003"},
    "tom": {"password": "admin123", "user_id": "user_004"},
    "lily": {"password": "pass321", "user_id": "user_005"},
}

_active_tokens: dict[str, str] = {}


def get_current_user_id(req=None):
    """Extract and validate the Bearer token, return user_id or None."""
    r = req or request
    auth = r.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    return _active_tokens.get(token)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    username = data.get("username", "").strip().lower()
    password = data.get("password", "").strip()

    cred = CREDENTIALS.get(username)
    if not cred or cred["password"] != password:
        return jsonify({"error": "Invalid username or password"}), 401

    token = uuid.uuid4().hex
    _active_tokens[token] = cred["user_id"]

    db = get_db()
    user = db.execute(
        "SELECT id, username, neighborhood, role FROM users WHERE id = ?",
        (cred["user_id"],),
    ).fetchone()

    return jsonify({"token": token, "user": dict(user)})


@auth_bp.route("/api/me", methods=["GET"])
def me():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    user = db.execute(
        "SELECT id, username, neighborhood, role FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(dict(user))


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        _active_tokens.pop(token, None)
    return jsonify({"ok": True})
