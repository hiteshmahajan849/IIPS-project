"""Application factory. Presentation layer wiring happens here: blueprint
registration, error pages, and shared template context (Chapter 7)."""
from pathlib import Path

from flask import Flask, render_template, session

from .config import Config
from .repository import db
from .utils.security import get_csrf_token


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_object)

    Path(app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from .controllers import admin_routes, auth_routes, dashboard_routes, feedback_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(feedback_routes.bp)
    app.register_blueprint(dashboard_routes.bp)
    app.register_blueprint(admin_routes.bp)

    @app.context_processor
    def inject_user():
        # csrf_token is generated (or reused) here on every request so that
        # every template -- not just the ones that pass it explicitly to
        # render_template -- has a valid, current token. This matters
        # because logging in calls session.clear(), which wipes out any
        # token issued before authentication.
        return {
            "current_role": session.get("role"),
            "current_name": session.get("name"),
            "csrf_token": get_csrf_token(),
        }

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors.html", code=403, message="You do not have access to this page."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors.html", code=404, message="Page not found."), 404

    @app.errorhandler(409)
    def conflict(_e):
        return render_template("errors.html", code=409, message="This action was already completed."), 409

    return app
