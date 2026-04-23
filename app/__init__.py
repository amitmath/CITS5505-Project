from flask import Flask, render_template

"""
Application factory function.
Creates and configures the Flask app instance.
Returns:
    Flask: The configured Flask app instance.
"""
def create_app():
    app = Flask(__name__)
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