from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
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

    # Register API blueprint
    from app.routes import api
    app.register_blueprint(api)

    # Route for index page
    @app.route("/")
    def index():
        return render_template("index.html")

    # Route for authentication page
    @app.route("/auth")
    def auth():
        return render_template("auth.html")

    # Route for dashboard page
    @app.route("/dashboard")
    def dashboard():
        from app.models import Project, Task, User
        user = User.query.first()
        projects = Project.query.filter_by(status="active").all()
        tasks = Task.query.filter_by(assignee_id=user.id).all() if user else []
        return render_template("dashboard.html", user=user, projects=projects, tasks=tasks)

    # Route for sprints page
    @app.route("/sprints")
    def sprints():
        return render_template("sprints.html")

    # Route for project page
    @app.route("/project")
    def project():
        return render_template("project.html")
    
    with app.app_context():
        db.create_all()

    return app
