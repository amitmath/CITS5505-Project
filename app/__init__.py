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
    from app.models import Project, Sprint, SprintCheckIn, Task, User

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
        active_project_count = Project.query.filter_by(status="active").count()
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
    @app.route("/sprints", methods=["GET", "POST"])
    def sprints():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        sprint_errors = []
        form_data = {}
        projects = Project.query.filter_by(status="active").order_by(Project.name.asc()).all()

        if request.method == "POST":
            form_data = request.form
            name = request.form.get("name", "").strip()
            project_id = request.form.get("project_id")
            goal = request.form.get("goal", "").strip()
            start_date_raw = request.form.get("start_date", "")
            end_date_raw = request.form.get("end_date", "")
            total_points_raw = request.form.get("total_story_points", "0")

            # Validate the modal form before adding a sprint to the database.
            project = db.session.get(Project, int(project_id)) if project_id and project_id.isdigit() else None
            if not project:
                sprint_errors.append("Please select a project.")
            if not name:
                sprint_errors.append("Sprint name is required.")

            try:
                start_date = date.fromisoformat(start_date_raw)
                end_date = date.fromisoformat(end_date_raw)
            except ValueError:
                start_date = None
                end_date = None
                sprint_errors.append("Please enter valid start and end dates.")

            try:
                total_story_points = int(total_points_raw)
            except ValueError:
                total_story_points = 0
                sprint_errors.append("Story points must be a number.")

            if start_date and end_date and end_date < start_date:
                sprint_errors.append("End date must be after the start date.")

            if total_story_points < 0:
                sprint_errors.append("Story points cannot be negative.")

            if not sprint_errors:
                sprint = Sprint(
                    project_id=project.id,
                    name=name,
                    goal=goal,
                    status="planned",
                    start_date=start_date,
                    end_date=end_date,
                    total_story_points=total_story_points,
                    completed_story_points=0,
                    velocity_points=0,
                )
                db.session.add(sprint)
                db.session.commit()
                return redirect(url_for("sprints"))

        # Load the current sprint and previous completed sprints for this page.
        active_sprint = Sprint.query.filter_by(status="active").order_by(Sprint.end_date.asc()).first()
        planned_sprints = Sprint.query.filter_by(status="planned").order_by(Sprint.start_date.asc()).all()
        completed_sprints = Sprint.query.filter_by(status="completed").order_by(Sprint.end_date.desc()).all()

        def progress_percent(completed_points, total_points):
            return round((completed_points / total_points) * 100, 1) if total_points else 0

        current_sprint = {
            "id": None,
            "project_name": "No project selected",
            "title": "No Active Sprint",
            "goal": "No active sprint has been created yet.",
            "velocity": "0 pts",
            "status": "Not Started",
            "progress": 0,
            "story_points": "0 of 0 story points completed",
            "days_left": 0,
            "day_label": "Days",
            "end_label": "No end date",
        }
        sprint_health = {
            "confidence_label": "No check-ins",
            "checkin_label": "0 check-ins",
            "workload_label": "No workload data",
            "blocker_count": 0,
            "help_count": 0,
        }
        recent_checkins = []

        if active_sprint:
            days_left = max((active_sprint.end_date - date.today()).days, 0)
            progress = progress_percent(
                active_sprint.completed_story_points,
                active_sprint.total_story_points,
            )
            current_sprint = {
                "id": active_sprint.id,
                "project_name": active_sprint.project.name,
                "title": f"Active Sprint ({active_sprint.name})",
                "goal": active_sprint.goal or "No sprint goal has been added yet.",
                "velocity": f"{active_sprint.velocity_points} pts",
                "status": active_sprint.status.replace("_", " ").title(),
                "progress": progress,
                "story_points": (
                    f"{active_sprint.completed_story_points} of "
                    f"{active_sprint.total_story_points} story points completed"
                ),
                "days_left": days_left,
                "day_label": "Day" if days_left == 1 else "Days",
                "end_label": active_sprint.end_date.strftime("Ends %b %d, %Y"),
            }

            # Sprint health is based on team check-ins saved for the active sprint.
            checkins = (
                SprintCheckIn.query
                .filter_by(sprint_id=active_sprint.id)
                .order_by(SprintCheckIn.checkin_date.desc())
                .all()
            )
            checkin_count = len(checkins)
            if checkins:
                average_confidence = round(
                    sum(checkin.confidence_level for checkin in checkins) / checkin_count,
                    1
                )
                average_workload = round(
                    sum(checkin.workload_level for checkin in checkins) / checkin_count,
                    1
                )
                blocker_count = sum(1 for checkin in checkins if checkin.blockers)
                help_count = sum(1 for checkin in checkins if checkin.needs_help)
                sprint_health = {
                    "confidence_label": f"{average_confidence}/5 confidence",
                    "checkin_label": f"{checkin_count} check-in" if checkin_count == 1 else f"{checkin_count} check-ins",
                    "workload_label": f"{average_workload}/5 workload",
                    "blocker_count": blocker_count,
                    "help_count": help_count,
                }

            recent_checkins = []
            for checkin in checkins[:5]:
                user_name = checkin.user.full_name if checkin.user else "Team member"
                recent_checkins.append({
                    "user_name": user_name,
                    "initial": user_name[:1].upper(),
                    "confidence": checkin.confidence_level,
                    "workload": checkin.workload_level,
                    "blockers": checkin.blockers or "No blockers added.",
                    "needs_help": checkin.needs_help,
                    "date": checkin.checkin_date.strftime("%b %d"),
                })

        # Planned sprints are shown separately so newly created sprints are easy to find.
        upcoming_sprints = []
        for sprint in planned_sprints:
            upcoming_sprints.append({
                "id": sprint.id,
                "name": sprint.name,
                "project_name": sprint.project.name,
                "duration": f"{sprint.start_date.strftime('%b %d')} - {sprint.end_date.strftime('%b %d')}",
                "story_points": sprint.total_story_points,
                "status": sprint.status.title(),
            })

        # Build simple rows for the past sprint table.
        past_sprints = []
        for sprint in completed_sprints:
            success_rate = progress_percent(
                sprint.completed_story_points,
                sprint.total_story_points,
            )
            past_sprints.append({
                "name": sprint.name,
                "duration": f"{sprint.start_date.strftime('%b %d')} - {sprint.end_date.strftime('%b %d')}",
                "status": sprint.status.replace("_", " ").title(),
                "story_points": f"{sprint.completed_story_points} / {sprint.total_story_points}",
                "success_rate": success_rate,
            })

        return render_template(
            "sprints.html",
            current_sprint=current_sprint,
            upcoming_sprints=upcoming_sprints,
            past_sprints=past_sprints,
            sprint_health=sprint_health,
            projects=projects,
            sprint_errors=sprint_errors,
            form_data=form_data,
            recent_checkins=recent_checkins,
        )

    @app.route("/sprints/<int:sprint_id>/check-in", methods=["POST"])
    def submit_sprint_checkin(sprint_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        sprint = db.session.get(Sprint, sprint_id)
        if not sprint or sprint.status != "active":
            flash("Check-ins can only be added for the active sprint.", "error")
            return redirect(url_for("sprints"))

        blockers = request.form.get("blockers", "").strip()
        needs_help = request.form.get("needs_help") == "on"

        try:
            confidence_level = int(request.form.get("confidence_level", ""))
            workload_level = int(request.form.get("workload_level", ""))
        except ValueError:
            flash("Confidence and workload must be selected.", "error")
            return redirect(url_for("sprints"))

        if confidence_level not in range(1, 6) or workload_level not in range(1, 6):
            flash("Confidence and workload must be between 1 and 5.", "error")
            return redirect(url_for("sprints"))

        today = date.today()
        # A user should only have one check-in per sprint per day, so update if it exists.
        checkin = SprintCheckIn.query.filter_by(
            sprint_id=sprint.id,
            user_id=g.user.id,
            checkin_date=today,
        ).first()

        if checkin is None:
            checkin = SprintCheckIn(
                sprint_id=sprint.id,
                user_id=g.user.id,
                checkin_date=today,
            )
            db.session.add(checkin)

        checkin.confidence_level = confidence_level
        checkin.workload_level = workload_level
        checkin.blockers = blockers
        checkin.needs_help = needs_help
        db.session.commit()

        flash("Sprint check-in saved.", "success")
        return redirect(url_for("sprints") + "#health")

    @app.route("/sprints/<int:sprint_id>/activate", methods=["POST"])
    def activate_sprint(sprint_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        sprint = db.session.get(Sprint, sprint_id)
        if sprint and sprint.status == "planned":
            # Keep only one active sprint at a time for the demo workflow.
            active_sprints = Sprint.query.filter_by(status="active").all()
            for active in active_sprints:
                active.status = "planned"

            sprint.status = "active"
            db.session.commit()

        return redirect(url_for("sprints"))

    @app.route("/sprints/<int:sprint_id>/complete", methods=["POST"])
    def complete_sprint(sprint_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        sprint = db.session.get(Sprint, sprint_id)
        if sprint and sprint.status == "active":
            # Use completed task points when possible before closing the sprint.
            completed_points = sum(
                task.story_points for task in sprint.tasks if task.status == "done"
            )
            if completed_points:
                sprint.completed_story_points = completed_points
            sprint.status = "completed"
            db.session.commit()

        return redirect(url_for("sprints"))

    # Route for project page
    @app.route("/project")
    def project():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        projects = [] 
        search_query = request.args.get("search", "").strip()

        try:
            query = Project.query.filter(
                func.lower(func.trim(Project.status)) == "active"
            )
            
            # Filter by search query if provided
            if search_query:
                query = query.filter(
                    func.lower(Project.name).contains(func.lower(search_query))
                )
            
            projects = query.all()
            
            # If exactly one project found and search was used, redirect to project detail with search query
            if search_query and len(projects) == 1:
                return redirect(url_for("project_detail", project_id=projects[0].id, search=search_query))

            print("COUNT:", len(projects))
            for p in projects:
                print(p.name, p.progress_percent)

        except Exception as e:
            print(f"Error fetching projects: {e}")

        return render_template("project.html", projects=projects, search_query=search_query)
    
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
        tasks = Task.query.filter_by(project_id=project.id).all()
        search_query = request.args.get("search", "").strip()

        return render_template(
        "project_detail.html",
        project=project,
        users=users,
        tasks=tasks,
        search_query=search_query
        )
    
    @app.route("/projects/<int:project_id>/backlog")
    def project_backlog(project_id):
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        project = Project.query.get_or_404(project_id)
        tasks = Task.query.filter_by(project_id=project.id).all()

        return render_template(
            "backlog.html",
            project=project,
            tasks=tasks
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

    #Route for backlog page
    
    @app.route("/backlog")
    def backlog():
        if g.user is None:
            return redirect(url_for("auth", mode="login"))

        tasks = Task.query.order_by(Task.created_at.desc()).all()

        return render_template(
          "backlog.html",
          project=None,
          tasks=tasks
        )
    
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
                upload_path = os.path.join(app.root_path, "static", "uploads", filename)
                avatar.save(upload_path)
                user.avatar_url = filename
            db.session.commit()
            success = True

        return render_template("profile.html", user=user, tasks=tasks, success=success)
    
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        if g.user is None:
            return redirect(url_for('auth', mode='login'))

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'save_profile':
                full_name = request.form.get('full_name', '').strip()
                email     = request.form.get('email', '').strip()
                job_title = request.form.get('job_title', '').strip()
                location  = request.form.get('location', '').strip()

                if not full_name:
                    flash('Full name cannot be empty.', 'danger')
                    return redirect(url_for('settings'))

                avatar_file = request.files.get('avatar')
                if avatar_file and avatar_file.filename:
                    filename = secure_filename(f"user_{g.user.id}_{avatar_file.filename}")
                    upload_path = os.path.join(app.root_path, 'static', 'uploads', filename)
                    avatar_file.save(upload_path)
                    g.user.avatar_url = filename

                g.user.full_name = full_name
                g.user.email     = email
                g.user.title     = job_title
                g.user.location  = location
                db.session.commit()
                flash('Settings saved successfully.', 'success')
                return redirect(url_for('settings'))


        return render_template('settings.html')

    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        if g.user is None:
            return redirect(url_for('auth', mode='login'))

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'save_profile':
                full_name = request.form.get('full_name', '').strip()
                email     = request.form.get('email', '').strip()
                job_title = request.form.get('job_title', '').strip()
                location  = request.form.get('location', '').strip()

                if not full_name:
                    flash('Full name cannot be empty.', 'danger')
                    return redirect(url_for('settings'))

                avatar_file = request.files.get('avatar')
                if avatar_file and avatar_file.filename:
                    filename = secure_filename(f"user_{g.user.id}_{avatar_file.filename}")
                    upload_path = os.path.join(app.root_path, 'static', 'uploads', filename)
                    avatar_file.save(upload_path)
                    g.user.avatar_url = filename

                g.user.full_name = full_name
                g.user.email     = email
                g.user.title     = job_title
                g.user.location  = location
                db.session.commit()
                flash('Settings saved successfully.', 'success')
                return redirect(url_for('settings'))

            elif action == 'change_password':
                current_password = request.form.get('current_password', '')
                new_password     = request.form.get('new_password', '')
                confirm_password = request.form.get('confirm_password', '')

                if not check_password_hash(g.user.password, current_password):
                    flash('Current password is incorrect.', 'danger')
                    return redirect(url_for('settings'))
                if len(new_password) < 8:
                    flash('New password must be at least 8 characters.', 'danger')
                    return redirect(url_for('settings'))
                if new_password != confirm_password:
                    flash('Passwords do not match.', 'danger')
                    return redirect(url_for('settings'))

                g.user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Password updated successfully.', 'success')
                return redirect(url_for('settings'))

        return render_template('settings.html')

    with app.app_context():
        db.create_all()

    return app
