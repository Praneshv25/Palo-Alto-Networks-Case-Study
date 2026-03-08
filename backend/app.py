import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        traceback.print_exc()
        from flask import jsonify
        response = jsonify({"error": str(e)})
        response.status_code = 500
        return response

    if test_config:
        app.config.update(test_config)


    from database import init_app
    init_app(app)

    from routes.auth import auth_bp
    from routes.reports import reports_bp
    from routes.votes import votes_bp
    from routes.circles import circles_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(votes_bp)
    app.register_blueprint(circles_bp)

    @app.route("/api/health")
    def health():
        ai_status = "unknown"
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "your_key_here":
                ai_status = "connected"
            else:
                ai_status = "no_api_key"
        except Exception:
            ai_status = "error"

        return jsonify({
            "status": "healthy",
            "ai_service": ai_status,
        })

    @app.route("/api/users")
    def get_users():
        from flask import request as req
        from database import get_db
        db = get_db()
        search = req.args.get("search", "").strip()
        if search:
            rows = db.execute(
                "SELECT id, username, neighborhood, role FROM users WHERE username LIKE ?",
                (f"%{search}%",),
            ).fetchall()
        else:
            rows = db.execute("SELECT id, username, neighborhood, role FROM users").fetchall()
        return jsonify([dict(r) for r in rows])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
