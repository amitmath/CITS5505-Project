import re

from flask import Flask, g, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config

# Create extension objects globally
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    """
    Application factory function.
    Creates and configures the Flask app instance.
    """
    app = Flask(__name__)

    # Load application settings from config.py
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so SQLAlchemy and migrations can detect them
    from app import models
    from app.models import Project, Task, User

    # Register API blueprint
    from app.routes import api
    app.register_blueprint(api)

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id else None
        if user_id and g.user is None:
            session.clear()

    # Route for index page
    @app.route("/")
    def index():
        return render_template("index.html")

    # Route for authentication page
    @app.route("/auth", methods=["GET", "POST"])
    def auth():
        active_form = request.args.get("mode", "register")
        errors = []
        form_data = {}

        if request.method == "POST":
            active_form = request.form.get("form_type", "login")
            form_data = request.form
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not email:
                errors.append("Email is required.")
            elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                errors.append("Please enter a valid email address.")

            if not password:
                errors.append("Password is required.")

            if active_form == "register":
                full_name = request.form.get("full_name", "").strip()
                confirm_password = request.form.get("confirm_password", "")

                if not full_name:
                    errors.append("Full name is required.")

                if password and len(password) < 6:
                    errors.append("Password must be at least 6 characters.")

                if password != confirm_password:
                    errors.append("Passwords do not match.")

                if not request.form.get("terms"):
                    errors.append("Please agree to the terms and privacy policy.")

                if email and User.query.filter_by(email=email).first():
                    errors.append("An account with this email already exists.")

                if not errors:
                    user = User(
                        full_name=full_name,
                        email=email,
                        password_hash=generate_password_hash(password),
                    )
                    db.session.add(user)
                    db.session.commit()
                    session["user_id"] = user.id
                    return redirect(url_for("dashboard"))

            else:
                user = User.query.filter_by(email=email).first() if email else None

                if not errors and (user is None or not check_password_hash(user.password_hash, password)):
                    errors.append("Invalid email or password.")

                if not errors:
                    session["user_id"] = user.id
                    return redirect(url_for("dashboard"))

        return render_template(
            "auth.html",
            active_form=active_form,
            errors=errors,
            form_data=form_data,
        )

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("auth", mode="login"))

    # Route for dashboard page
    @app.route("/dashboard")
    def dashboard():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        user = g.user
        projects = Project.query.filter_by(status="active").all()
        tasks = Task.query.filter_by(assignee_id=user.id).all() if user else []
        return render_template("dashboard.html", user=user, projects=projects, tasks=tasks)

    # Route for sprints page
    @app.route("/sprints")
    def sprints():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        return render_template("sprints.html")

    # Route for project page
    @app.route("/project")
    def project():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        return render_template("project.html")

    with app.app_context():
        db.create_all()

    return app
