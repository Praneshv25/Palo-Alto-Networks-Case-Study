import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)

    if test_config:
        app.config.update(test_config)


    from database import init_app
    init_app(app)

    from routes.reports import reports_bp
    from routes.votes import votes_bp
    app.register_blueprint(reports_bp)
    app.register_blueprint(votes_bp)

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
        from database import get_db
        db = get_db()
        rows = db.execute("SELECT id, username, neighborhood, role FROM users").fetchall()
        return jsonify([dict(r) for r in rows])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
