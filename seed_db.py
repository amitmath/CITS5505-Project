from app import create_app, db
from app.models import User, Project, Task
from datetime import date
from werkzeug.security import generate_password_hash

app = create_app()
# this file is added to populate some test data into the database. 

with app.app_context():

    # Clear existing data
    Task.query.delete()
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
    # Create sample tasks
    # -------------------------

    t1 = Task(
        title="Update API Documentation",
        project_id=p1.id,
        assignee_id=user1.id,
        status="in_progress",
        priority="high",
        due_date=date(2026, 10, 24),
    )

    t2 = Task(
        title="Finalize UI Kit Components",
        project_id=p2.id,
        assignee_id=user1.id,
        status="todo",
        priority="medium",
        due_date=date(2026, 10, 26),
    )

    t3 = Task(
        title="Database Indexing Review",
        project_id=p3.id,
        assignee_id=user1.id,
        status="todo",
        priority="low",
        due_date=date(2026, 10, 28),
    )

    db.session.add_all([t1, t2, t3])
    db.session.commit()

    print("Tasks seeded successfully.")
