import re
from datetime import date, datetime

import os
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask import Flask, app, flash, g, redirect, render_template, request, session, url_for
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
    from app.models import Project, Sprint, Task, User

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
        projects = (
        Project.query
            .filter_by(status="active")
            .order_by(Project.created_at.desc())
            .limit(3)
            .all()
        )
        # Used by the dashboard summary card to show the live project count.
        active_project_count = len(projects)
        tasks = Task.query.filter_by(assignee_id=user.id).all() if user else []
        # Show the user's assigned tasks in due-date order on the dashboard.
        tasks = sorted(tasks, key=lambda task: (task.due_date is None, task.due_date or date.max))
        assigned_task_count = len(tasks)

        # Default values keep the dashboard working even when no sprint exists yet.
        sprint_summary = {
            "name": "No active sprint",
            "days_left_label": "No sprint scheduled",
            "velocity_percent": 0,
            "completed": 0,
            "in_progress": 0,
            "blockers": 0,
            "completed_percent": 0,
            "in_progress_percent": 0,
            "blocker_percent": 0,
        }

        # Find the current active sprint and calculate the dashboard health numbers.
        active_sprint = Sprint.query.filter_by(status="active").order_by(Sprint.end_date.asc()).first()
        if active_sprint:
            sprint_tasks = Task.query.filter_by(sprint_id=active_sprint.id).all()
            total_tasks = len(sprint_tasks)
            completed_count = sum(1 for task in sprint_tasks if task.status == "done")
            in_progress_count = sum(1 for task in sprint_tasks if task.status == "in_progress")
            blocker_count = sum(1 for task in sprint_tasks if task.status == "blocker")

            if active_sprint.total_story_points:
                velocity_percent = round(
                    (active_sprint.completed_story_points / active_sprint.total_story_points) * 100
                )
            else:
                velocity_percent = round((completed_count / total_tasks) * 100) if total_tasks else 0

            def task_percent(count):
                return round((count / total_tasks) * 100) if total_tasks else 0

            days_left = (active_sprint.end_date - date.today()).days
            if days_left < 0:
                days_left_label = "Sprint ended"
            elif days_left == 1:
                days_left_label = "1 day left"
            else:
                days_left_label = f"{days_left} days left"

            sprint_summary = {
                "name": active_sprint.name,
                "days_left_label": days_left_label,
                "velocity_percent": velocity_percent,
                "completed": completed_count,
                "in_progress": in_progress_count,
                "blockers": blocker_count,
                "completed_percent": task_percent(completed_count),
                "in_progress_percent": task_percent(in_progress_count),
                "blocker_percent": task_percent(blocker_count),
            }

        return render_template(
            "dashboard.html",
            user=user,
            projects=projects,
            active_project_count=active_project_count,
            sprint_summary=sprint_summary,
            assigned_task_count=assigned_task_count,
            tasks=tasks,
        )

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

        projects = [] 

        try:
            projects = Project.query.filter(
                func.lower(func.trim(Project.status)) == "active"
            ).all()

            print("COUNT:", len(projects))
            for p in projects:
                print(p.name, p.progress_percent)

        except Exception as e:
            print(f"Error fetching projects: {e}")

        return render_template("project.html", projects=projects)
    
    @app.route("/projects/create", methods=["POST"])
    def create_project():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "active").strip()

        if not name:
            flash("Project name is required.", "error")
            return redirect(url_for("project"))

        new_project = Project(
            name=name,
            description=description,
            status=status,
            health_status="healthy",
            progress_percent=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.session.add(new_project)
        db.session.commit()

        flash("Project created successfully.", "success")
        return redirect(url_for("project"))
    
    @app.route("/projects/<int:project_id>")
    def project_detail(project_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        project = Project.query.get_or_404(project_id)
        users = User.query.filter_by(is_active=True).all()

        return render_template(
        "project_detail.html",
        project=project,
        users=users
        )
    
    @app.route("/projects/<int:project_id>/assign-users", methods=["POST"])
    def assign_project_users(project_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        project = Project.query.get_or_404(project_id)

        selected_user_ids = request.form.getlist("user_ids")
        selected_user_ids = [int(uid) for uid in selected_user_ids]

        selected_users = User.query.filter(User.id.in_(selected_user_ids)).all()

        project.assigned_users = selected_users

        db.session.commit()

        flash("Project users updated successfully.", "success")
        return redirect(url_for("project_detail", project_id=project.id))
    
    @app.route("/projects/<int:project_id>/edit", methods=["POST"])
    def edit_project(project_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        project = Project.query.get_or_404(project_id)

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "active").strip()
        health_status = request.form.get("health_status", "healthy").strip()

        if not name:
            flash("Project name is required.", "error")
            return redirect(url_for("project_detail", project_id=project.id))

        project.name = name
        project.description = description
        project.status = status
        project.health_status = health_status

        db.session.commit()

        flash("Project updated successfully.", "success")
        return redirect(url_for("project_detail", project_id=project.id))
    
    @app.route("/projects/<int:project_id>/delete", methods=["POST"])
    def delete_project(project_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        project = Project.query.get_or_404(project_id)

        db.session.delete(project)
        db.session.commit()

        flash("Project deleted successfully.", "success")
        return redirect(url_for("project"))
    
    # Route for user profile page
    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))
        
        user = g.user
        tasks = Task.query.filter_by(assignee_id=user.id).all()
        success = False

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            if full_name:
                user.full_name = full_name
            user.title = request.form.get("title", user.title)
            user.location = request.form.get("location", user.location)
            user.bio = request.form.get("bio", user.bio)
            avatar = request.files.get("avatar")
            if avatar and avatar.filename:
                filename = secure_filename(f"user_{user.id}_{avatar.filename}")
                upload_path = os.path.join("app", "static", "uploads", filename)
                avatar.save(upload_path)
                user.avatar_url = url_for("static", filename=f"uploads/{filename}")
            db.session.commit()
            success = True

        return render_template("profile.html", user=user, tasks=tasks, success=success)

    with app.app_context():
        db.create_all()

    return app
