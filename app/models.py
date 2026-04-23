from app import db

from datetime import datetime, date
from app import db

class ProjectMembership(db.Model):
    __tablename__ = "project_memberships"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    role = db.Column(db.String(50), nullable=False)
    capacity_percent = db.Column(db.Integer, default=100)
    is_project_lead = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="memberships")
    user = db.relationship("User", back_populates="project_memberships")


class UserSkill(db.Model):
    __tablename__ = "user_skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill_tags.id"), nullable=False)

    user = db.relationship("User", back_populates="user_skills")
    skill = db.relationship("SkillTag", back_populates="user_skills")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    title = db.Column(db.String(80))
    bio = db.Column(db.Text)
    location = db.Column(db.String(120))
    timezone = db.Column(db.String(80))
    avatar_url = db.Column(db.String(255))

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project_memberships = db.relationship("ProjectMembership", back_populates="user", cascade="all, delete-orphan")
    assigned_tasks = db.relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    created_tasks = db.relationship("Task", back_populates="creator", foreign_keys="Task.created_by")
    checkins = db.relationship("CheckIn", back_populates="user")
    help_requests_created = db.relationship("HelpRequest", back_populates="requester", foreign_keys="HelpRequest.requester_id")
    help_requests_assigned = db.relationship("HelpRequest", back_populates="helper", foreign_keys="HelpRequest.helper_id")
    user_skills = db.relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")


class SkillTag(db.Model):
    __tablename__ = "skill_tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    user_skills = db.relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)

    status = db.Column(db.String(30), nullable=False, default="active")
    health_status = db.Column(db.String(30), default="healthy")
    progress_percent = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships = db.relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")
    sprints = db.relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    tasks = db.relationship("Task", back_populates="project", cascade="all, delete-orphan")
    blockers = db.relationship("Blocker", back_populates="project", cascade="all, delete-orphan")


class Sprint(db.Model):
    __tablename__ = "sprints"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    goal = db.Column(db.Text)
    status = db.Column(db.String(30), default="planned")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    total_story_points = db.Column(db.Integer, default=0)
    completed_story_points = db.Column(db.Integer, default=0)
    velocity_points = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="sprints")
    tasks = db.relationship("Task", back_populates="sprint")
    blockers = db.relationship("Blocker", back_populates="sprint", cascade="all, delete-orphan")
    checkins = db.relationship("CheckIn", back_populates="sprint", cascade="all, delete-orphan")
    help_requests = db.relationship("HelpRequest", back_populates="sprint", cascade="all, delete-orphan")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.id"), nullable=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    task_code = db.Column(db.String(30), unique=True)

    priority = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(30), default="backlog")
    story_points = db.Column(db.Integer, default=0)

    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship("Project", back_populates="tasks")
    sprint = db.relationship("Sprint", back_populates="tasks")
    assignee = db.relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    creator = db.relationship("User", back_populates="created_tasks", foreign_keys=[created_by])
    blockers = db.relationship("Blocker", back_populates="task")


class Blocker(db.Model):
    __tablename__ = "blockers"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.id"), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="blockers")
    sprint = db.relationship("Sprint", back_populates="blockers")
    task = db.relationship("Task", back_populates="blockers")


class CheckIn(db.Model):
    __tablename__ = "checkins"

    id = db.Column(db.Integer, primary_key=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    checkin_date = db.Column(db.Date, nullable=False, default=date.today)
    mood = db.Column(db.String(20))
    workload_status = db.Column(db.String(20))
    status_update = db.Column(db.Text)

    sprint = db.relationship("Sprint", back_populates="checkins")
    user = db.relationship("User", back_populates="checkins")


class HelpRequest(db.Model):
    __tablename__ = "help_requests"

    id = db.Column(db.Integer, primary_key=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    helper_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sprint = db.relationship("Sprint", back_populates="help_requests")
    requester = db.relationship("User", back_populates="help_requests_created", foreign_keys=[requester_id])
    helper = db.relationship("User", back_populates="help_requests_assigned", foreign_keys=[helper_id])
    """
    Project model for storing project workspace details.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Active")

    def __repr__(self):
        return f"<Project {self.name}>"