"""
INSYTE — E-Commerce Customer Behaviour Analytics
Flask Application Factory & Lifecycle Controller
"""

import atexit
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.database import init_pool, close_pool
from app.routes.api import api_bp
from app.routes.main import main_bp

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Enable CORS for local and staging access
    CORS(app)

    # Initialize Oracle 23ai Connection Pool
    with app.app_context():
        init_pool()

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Global Error Handlers (Never expose raw stack traces to the user)
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "An internal database or query error occurred", "status": 500}), 500

    # Graceful Pool Teardown on Process Exit
    atexit.register(close_pool)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
