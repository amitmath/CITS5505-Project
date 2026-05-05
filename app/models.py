from datetime import datetime
from app import db

project_users = db.Table(
    "project_users",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role", db.String(80), nullable=True),
    db.Column("assigned_at", db.DateTime, default=datetime.utcnow),
)

class User(db.Model):
    """
    Represents a user/team member in the Agile PM system.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    title = db.Column(db.String(80), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    timezone = db.Column(db.String(80), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assigned_tasks = db.relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assignee_id"
    )

    created_tasks = db.relationship(
        "Task",
        back_populates="creator",
        foreign_keys="Task.created_by"
    )

    projects = db.relationship(
        "Project",
        secondary=project_users,
        back_populates="assigned_users"
    )


    def __repr__(self):
        return f"<User {self.full_name}>"

class Project(db.Model):
    """
    Represents a project such as Quantum ERP or Starlight Mobile.
    """
    __tablename__ = "projects"

    @property
    def calculated_progress(self):
        total_tasks = len(self.tasks)

        if total_tasks == 0:
            return 0

        completed_tasks = sum(1 for task in self.tasks if task.status == "done")

        return round((completed_tasks / total_tasks) * 100)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(30), nullable=False, default="active")
    health_status = db.Column(db.String(30), nullable=True, default="healthy")
    progress_percent = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    sprints = db.relationship(
        "Sprint",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    tasks = db.relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    assigned_users = db.relationship(
        "User",
        secondary=project_users,
        back_populates="projects"
    )

    def __repr__(self):
        return f"<Project {self.name}>"

class Sprint(db.Model):
    """
    Represents a sprint within a project.
    Each sprint belongs to exactly one project.
    """
    __tablename__ = "sprints"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False
    )

    name = db.Column(db.String(120), nullable=False)
    goal = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="planned")  # planned, active, completed

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    total_story_points = db.Column(db.Integer, default=0)
    completed_story_points = db.Column(db.Integer, default=0)
    velocity_points = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    project = db.relationship("Project", back_populates="sprints")

    tasks = db.relationship(
        "Task",
        back_populates="sprint"
    )

    def __repr__(self):
        return f"<Sprint {self.name}>"

class Task(db.Model):
    """
    Represents a task/backlog item in the system.
    A task belongs to one project and may optionally belong to a sprint.
    A task may also be assigned to a user.
    """
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False
    )

    sprint_id = db.Column(
        db.Integer,
        db.ForeignKey("sprints.id"),
        nullable=True
    )

    assignee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_code = db.Column(db.String(30), unique=True, nullable=True)

    priority = db.Column(db.String(20), default="medium")   # low, medium, high
    status = db.Column(db.String(30), default="backlog")    # backlog, todo, in_progress, done
    story_points = db.Column(db.Integer, default=0)

    due_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    project = db.relationship("Project", back_populates="tasks")
    sprint = db.relationship("Sprint", back_populates="tasks")

    assignee = db.relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assignee_id]
    )

    creator = db.relationship(
        "User",
        back_populates="created_tasks",
        foreign_keys=[created_by]
    )

    def __repr__(self):
        return f"<Task {self.title}>"
    