from flask import Blueprint, jsonify, render_template, g
from sqlalchemy import func
from app.models import Project, User, Sprint, Task, SprintCheckIn

api = Blueprint("api", __name__)

def require_auth():
    """Helper function to check authentication for API endpoints."""
    if g.user is None:
        return None
    return g.user

# Analytics API endpoints - all require authentication
def check_auth():
    """Check if user is authenticated, return 401 if not."""
    if g.user is None:
        return jsonify({"error": "Unauthorized"}), 401

@api.route("/api/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "title": u.title,
            "location": u.location
        }
        for u in users
    ])

@api.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "title": user.title,
        "location": user.location
    })

# Analytics API endpoints - all require authentication
@api.route("/api/analytics/sprint-velocity", methods=["GET"])
def get_sprint_velocity():
    """Get sprint velocity data for all completed sprints."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    sprints = Sprint.query.filter(
        Sprint.status == "completed"
    ).order_by(Sprint.start_date).all()
    
    data = {
        "sprint_names": [s.name for s in sprints],
        "velocities": [s.completed_story_points or 0 for s in sprints],
        "planned_points": [s.total_story_points or 0 for s in sprints]
    }
    return jsonify(data)

@api.route("/api/analytics/sprint-burndown/<int:sprint_id>", methods=["GET"])
def get_sprint_burndown(sprint_id):
    """Get burndown data for a specific sprint."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    sprint = Sprint.query.get_or_404(sprint_id)
    tasks = Task.query.filter_by(sprint_id=sprint_id).all()
    
    # Calculate remaining story points by status
    remaining = {
        "backlog": sum(t.story_points for t in tasks if t.status == "backlog"),
        "todo": sum(t.story_points for t in tasks if t.status == "todo"),
        "in_progress": sum(t.story_points for t in tasks if t.status == "in_progress"),
        "done": sum(t.story_points for t in tasks if t.status == "done"),
        "blocker": sum(t.story_points for t in tasks if t.status == "blocker")
    }
    
    return jsonify({
        "sprint_name": sprint.name,
        "total_points": sprint.total_story_points or 0,
        "completed_points": sprint.completed_story_points or 0,
        "remaining_breakdown": remaining,
        "percent_complete": round((sprint.completed_story_points or 0) / max(sprint.total_story_points or 1, 1) * 100)
    })

@api.route("/api/analytics/task-distribution", methods=["GET"])
def get_task_distribution():
    """Get task distribution by status across all projects."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    statuses = ["backlog", "todo", "in_progress", "blocker", "done"]
    distribution = {}
    
    for status in statuses:
        count = Task.query.filter_by(status=status).count()
        distribution[status] = count
    
    return jsonify(distribution)

@api.route("/api/analytics/team-workload", methods=["GET"])
def get_team_workload():
    """Get task workload distribution across team members."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    users = User.query.all()
    workload = {}
    
    for user in users:
        assigned_tasks = Task.query.filter_by(assignee_id=user.id).all()
        task_count = len(assigned_tasks)
        story_points = sum(t.story_points or 0 for t in assigned_tasks)
        
        workload[user.full_name] = {
            "task_count": task_count,
            "story_points": story_points
        }
    
    return jsonify(workload)

@api.route("/api/analytics/sprint-health/<int:sprint_id>", methods=["GET"])
def get_sprint_health(sprint_id):
    """Get sprint health metrics (team confidence and workload)."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    sprint = Sprint.query.get_or_404(sprint_id)
    checkins = SprintCheckIn.query.filter_by(sprint_id=sprint_id).all()
    
    if not checkins:
        return jsonify({
            "avg_confidence": 0,
            "avg_workload": 0,
            "blockers_count": 0,
            "help_needed_count": 0,
            "team_size": 0
        })
    
    avg_confidence = sum(c.confidence_level for c in checkins) / len(checkins)
    avg_workload = sum(c.workload_level for c in checkins) / len(checkins)
    blockers_count = sum(1 for c in checkins if c.blockers)
    help_needed = sum(1 for c in checkins if c.needs_help)
    
    return jsonify({
        "sprint_name": sprint.name,
        "avg_confidence": round(avg_confidence, 1),
        "avg_workload": round(avg_workload, 1),
        "blockers_count": blockers_count,
        "help_needed_count": help_needed,
        "team_size": len(checkins)
    })

@api.route("/api/analytics/priority-distribution", methods=["GET"])
def get_priority_distribution():
    """Get task distribution by priority."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    priorities = ["low", "medium", "high"]
    distribution = {}
    
    for priority in priorities:
        count = Task.query.filter_by(priority=priority).count()
        distribution[priority] = count
    
    return jsonify(distribution)

@api.route("/api/analytics/project-progress", methods=["GET"])
def get_project_progress():
    """Get progress metrics for all projects."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    projects = Project.query.all()
    progress_data = []
    
    for project in projects:
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for t in project.tasks if t.status == "done")
        progress_percent = round((completed_tasks / max(total_tasks, 1)) * 100)
        
        progress_data.append({
            "name": project.name,
            "progress": progress_percent,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "status": project.status
        })
    
    return jsonify(progress_data)

@api.route("/api/analytics/active-sprints-summary", methods=["GET"])
def get_active_sprints_summary():
    """Get summary of all active sprints."""
    auth_check = check_auth()
    if auth_check:
        return auth_check
    active_sprints = Sprint.query.filter_by(status="active").all()
    
    sprints_data = []
    for sprint in active_sprints:
        tasks = Task.query.filter_by(sprint_id=sprint.id).all()
        done_count = sum(1 for t in tasks if t.status == "done")
        total_count = len(tasks)
        
        sprints_data.append({
            "id": sprint.id,
            "name": sprint.name,
            "project_id": sprint.project_id,
            "completion_percent": round((done_count / max(total_count, 1)) * 100),
            "completed_points": sprint.completed_story_points or 0,
            "total_points": sprint.total_story_points or 0,
            "task_count": total_count,
            "completed_tasks": done_count
        })
    
    return jsonify(sprints_data)