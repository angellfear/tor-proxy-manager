import os
import secrets
from pathlib import Path
from flask import Flask, session, request, redirect

def create_app():
    app = Flask(__name__)
    key = os.environ.get('FLASK_SECRET_KEY')
    if not key:
        key_path = Path('/config/secret_key')
        if key_path.exists():
            key = key_path.read_text().strip()
        else:
            key = secrets.token_hex(32)
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_text(key)
    app.secret_key = key
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.config import config_bp
    from app.routes.bridges import bridges_bp
    from app.routes.torrc_editor import torrc_bp
    from app.routes.logs import logs_bp
    from app.api.routes import api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(bridges_bp)
    app.register_blueprint(torrc_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(api_bp)
    @app.before_request
    def require_login():
        from app.utils.config import load_settings
        settings = load_settings()
        if not settings.get('require_auth', False):
            return
        if request.path.startswith('/static') or request.path == '/login' or request.path == '/api/status':
            return
        if 'user' not in session:
            return redirect('/login')
    @app.context_processor
    def inject_user():
        from app.utils.config import load_settings
        settings = load_settings()
        if not settings.get('require_auth', False):
            return dict(current_user='Tor Proxy')
        return dict(current_user=session.get('user'))
    @app.after_request
    def add_csp(response):
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    return app
