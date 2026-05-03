from app import create_app, db
from app.models import User, Project, Sprint, Task
from datetime import date
from werkzeug.security import generate_password_hash

app = create_app()
# this file is added to populate some test data into the database. 

with app.app_context():

    # Clear existing data
    Task.query.delete()
    Sprint.query.delete()
    Project.query.delete()
    User.query.delete()
    db.session.commit()

    # -------------------------
    # Create sample users
    # -------------------------

    user1 = User(
        full_name="Liam Thompson",
        email="liam.thompson@example.com",
        password_hash=generate_password_hash("password123"),
        title="Project Lead",
        location="Perth, Australia",
        timezone="Australia/Perth",
        avatar_url="https://example.com/avatars/liam.png",
    )

    user2 = User(
        full_name="Olivia Walker",
        email="olivia.walker@example.com",
        password_hash=generate_password_hash("password123"),
        title="UI/UX Designer",
        location="Sydney, Australia",
        timezone="Australia/Sydney",
        avatar_url="https://example.com/avatars/olivia.png",
    )

    user3 = User(
        full_name="Noah Williams",
        email="noah.williams@example.com",
        password_hash=generate_password_hash("password123"),
        title="Backend Developer",
        location="Melbourne, Australia",
        timezone="Australia/Melbourne",
        avatar_url="https://example.com/avatars/noah.png",
    )

    db.session.add_all([user1, user2, user3])
    db.session.commit()

    print("Users seeded successfully.")

    # -------------------------
    # Create sample projects
    # -------------------------

    p1 = Project(
        name="Quantum ERP",
        description="Infrastructure optimization for retail partners.",
        status="active",
        health_status="healthy",
    )

    p2 = Project(
        name="Starlight Mobile",
        description="Redesigning the guest checkout experience.",
        status="active",
        health_status="at-risk",
    )

    p3 = Project(
        name="Core Database",
        description="Migration to high-availability clusters.",
        status="active",
        health_status="healthy",
    )

    db.session.add_all([p1, p2, p3])
    db.session.commit()

    print("Projects seeded successfully.")

    # -------------------------
    # Create sample sprints
    # -------------------------

    # These sprints make the dashboard and sprints page show realistic data.
    sprint1 = Sprint(
        project_id=p1.id,
        name="Sprint 12",
        goal="Finalize core financial engine integration and test the main API workflow.",
        status="active",
        start_date=date(2026, 10, 14),
        end_date=date(2026, 10, 28),
        total_story_points=62,
        completed_story_points=24,
        velocity_points=42,
    )

    sprint2 = Sprint(
        project_id=p1.id,
        name="Sprint 11",
        goal="Complete project setup and prepare first user testing cycle.",
        status="completed",
        start_date=date(2026, 9, 30),
        end_date=date(2026, 10, 13),
        total_story_points=54,
        completed_story_points=50,
        velocity_points=50,
    )

    sprint3 = Sprint(
        project_id=p2.id,
        name="Sprint 5",
        goal="Improve checkout screens and review mobile layout issues.",
        status="completed",
        start_date=date(2026, 9, 16),
        end_date=date(2026, 9, 29),
        total_story_points=40,
        completed_story_points=36,
        velocity_points=36,
    )

    db.session.add_all([sprint1, sprint2, sprint3])
    db.session.commit()

    print("Sprints seeded successfully.")

    # -------------------------
    # Create sample tasks
    # -------------------------

    t1 = Task(
        title="Update API Documentation",
        project_id=p1.id,
        sprint_id=sprint1.id,
        assignee_id=user1.id,
        status="in_progress",
        priority="high",
        story_points=8,
        due_date=date(2026, 10, 24),
    )

    t2 = Task(
        title="Finalize UI Kit Components",
        project_id=p2.id,
        sprint_id=sprint1.id,
        assignee_id=user1.id,
        status="todo",
        priority="medium",
        story_points=5,
        due_date=date(2026, 10, 26),
    )

    t3 = Task(
        title="Database Indexing Review",
        project_id=p3.id,
        sprint_id=sprint1.id,
        assignee_id=user1.id,
        status="blocker",
        priority="low",
        story_points=11,
        due_date=date(2026, 10, 28),
    )

    db.session.add_all([t1, t2, t3])
    db.session.commit()

    print("Tasks seeded successfully.")
