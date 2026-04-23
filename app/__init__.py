from flask import Flask, render_template

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/auth")
    def auth():
        return render_template("auth.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/project")
    def project():
        return render_template("project.html")

    return app