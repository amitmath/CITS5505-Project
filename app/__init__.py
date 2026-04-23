from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Create the SQLAlchemy database object globally
db = SQLAlchemy()
migrate = Migrate()

"""
Application factory function.
Creates and configures the Flask app instance.
Returns:
    Flask: The configured Flask app instance.
"""
def create_app():
    app = Flask(__name__)

    # load application settings from config.py
    app.config.from_object(Config)

    # initialize SQLAlchemy with this app instance
    db.init_app(app)

    # initialize Flask-Migrate with the app and database
    migrate.init_app(app, db)

    # import models so SQLAlchemy and migrations can detect them
    from app import models
    
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
        return render_template("dashboard.html")

    # Route for project page
    @app.route("/project")
    def project():
        return render_template("project.html")

    return app