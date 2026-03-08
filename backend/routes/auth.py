import uuid
from flask import Blueprint, request, jsonify
from database import get_db

auth_bp = Blueprint("auth", __name__)

_active_tokens: dict[str, str] = {}

_USER_FIELDS = "id, username, neighborhood, role, lat, lng"


def get_current_user_id(req=None):
    """Extract and validate the Bearer token, return user_id or None."""
    r = req or request
    auth = r.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    return _active_tokens.get(token)


def _user_dict(row):
    d = dict(row)
    # Ensure numeric lat/lng are proper floats or None
    d["lat"] = float(d["lat"]) if d.get("lat") is not None else None
    d["lng"] = float(d["lng"]) if d.get("lng") is not None else None
    return d


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    username = data.get("username", "").strip().lower()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db = get_db()
    row = db.execute(
        f"SELECT {_USER_FIELDS}, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if not row or row["password_hash"] != password:
        return jsonify({"error": "Invalid username or password"}), 401

    token = uuid.uuid4().hex
    _active_tokens[token] = row["id"]

    user = db.execute(
        f"SELECT {_USER_FIELDS} FROM users WHERE id = ?", (row["id"],)
    ).fetchone()
    return jsonify({"token": token, "user": _user_dict(user)})


@auth_bp.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    username = data.get("username", "").strip().lower()
    password = data.get("password", "").strip()
    neighborhood = data.get("neighborhood", "").strip()
    lat = data.get("lat")
    lng = data.get("lng")

    if not username:
        return jsonify({"error": "Username is required"}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not neighborhood:
        return jsonify({"error": "Neighborhood is required"}), 400

    # Validate lat/lng if provided
    try:
        lat = float(lat) if lat is not None else None
        lng = float(lng) if lng is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid lat/lng values"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return jsonify({"error": "Username already taken"}), 409

    user_id = f"user_{uuid.uuid4().hex[:8]}"
    pw_hash = password

    db.execute(
        "INSERT INTO users (id, username, neighborhood, role, password_hash, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, neighborhood, "User", pw_hash, lat, lng),
    )
    db.commit()

    token = uuid.uuid4().hex
    _active_tokens[token] = user_id

    user = db.execute(
        f"SELECT {_USER_FIELDS} FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return jsonify({"token": token, "user": _user_dict(user)}), 201


@auth_bp.route("/api/me", methods=["GET"])
def me():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    db = get_db()
    user = db.execute(
        f"SELECT {_USER_FIELDS} FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(_user_dict(user))


@auth_bp.route("/api/me/location", methods=["PATCH"])
def update_location():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    try:
        lat = float(data["lat"])
        lng = float(data["lng"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Fields 'lat' and 'lng' must be numbers"}), 400

    db = get_db()
    db.execute("UPDATE users SET lat = ?, lng = ? WHERE id = ?", (lat, lng, user_id))
    db.commit()

    user = db.execute(
        f"SELECT {_USER_FIELDS} FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return jsonify(_user_dict(user))


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        _active_tokens.pop(token, None)
    return jsonify({"ok": True})
