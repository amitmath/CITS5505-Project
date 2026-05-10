from app import create_app, db
from app.models import User, Project, Sprint, SprintCheckIn, Task, project_users
from datetime import date, datetime
from werkzeug.security import generate_password_hash

app = create_app()
# this file is added to populate some test data into the database. 

with app.app_context():

    # Clear existing data
    SprintCheckIn.query.delete()
    Task.query.delete()
    db.session.execute(project_users.delete())
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
        avatar_url="liam_profile.avif",
    )

    user2 = User(
        full_name="Olivia Walker",
        email="olivia.walker@example.com",
        password_hash=generate_password_hash("password123"),
        title="UI/UX Designer",
        location="Sydney, Australia",
        timezone="Australia/Sydney",
        avatar_url="amina.png",
    )

    user3 = User(
        full_name="Noah Williams",
        email="noah.williams@example.com",
        password_hash=generate_password_hash("password123"),
        title="Backend Developer",
        location="Melbourne, Australia",
        timezone="Australia/Melbourne",
        avatar_url="noah_profile.avif",
    )

    user4 = User(
        full_name="testUser",
        email="test@gmail.com",
        password_hash=generate_password_hash("password123"),
        title="Software Engineer",
        location="Perth, Australia",
        timezone="Perth/Melbourne",
        avatar_url="user_5_pngtree-user-profile-avatar-png-image_10211467.png",
    )

    db.session.add_all([user1, user2, user3, user4])
    db.session.commit()

    print("Users seeded successfully.")

    # -------------------------
    # Create sample projects
    # -------------------------

    projects = [
        Project(
            id=1,
            name="Quantum ERP",
            description="Infrastructure optimization for retail partners.",
            status="active",
            health_status="healthy",
            progress_percent=0,
            created_at=datetime(2026, 4, 29, 3, 43, 57, 977348),
            updated_at=datetime(2026, 4, 29, 3, 43, 57, 977351),
        ),
        Project(
            id=2,
            name="Starlight Mobile",
            description="Redesigning the guest checkout experience.",
            status="active",
            health_status="at-risk",
            progress_percent=0,
            created_at=datetime(2026, 4, 29, 3, 43, 57, 977352),
            updated_at=datetime(2026, 4, 29, 3, 43, 57, 977353),
        ),
        Project(
            id=3,
            name="Core Database",
            description="Migration to high-availability clusters.",
            status="active",
            health_status="healthy",
            progress_percent=0,
            created_at=datetime(2026, 4, 29, 3, 43, 57, 977354),
            updated_at=datetime(2026, 4, 29, 3, 43, 57, 977355),
        ),
        Project(
            id=4,
            name="test project",
            description="This is a test description of the test project. Editing the description to test",
            status="inactive",
            health_status="healthy",
            progress_percent=0,
            created_at=datetime(2026, 5, 3, 17, 26, 13, 408319),
            updated_at=datetime(2026, 5, 4, 9, 4, 24, 635972),
        ),
        Project(
            id=6,
            name="Test Project 3",
            description="This is a Project created for testing purposes.",
            status="active",
            health_status="healthy",
            progress_percent=0,
            created_at=datetime(2026, 5, 3, 17, 33, 44, 728509),
            updated_at=datetime(2026, 5, 4, 9, 15, 51, 857306),
        ),
    ]

    db.session.add_all(projects)
    db.session.commit()

    print("Projects seeded successfully.")

    # -------------------------
    # Create sample sprints
    # -------------------------

    # These sprints make the dashboard and sprints page show realistic data.
    sprint1 = Sprint(
        project_id=1,
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
        project_id=1,
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
        project_id=2,
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

    tasks = [
    Task(
        id=1,
        project_id=1,
        assignee_id=1,
        title="Update API Documentation",
        priority="high",
        status="in_progress",
        sprint_id=sprint1.id,
        story_points=8,
        due_date=date(2026, 10, 24),
        created_at=datetime(2026, 4, 29, 3, 43, 57, 995091),
        updated_at=datetime(2026, 4, 29, 3, 43, 57, 995093),
    ),
    Task(
        id=2,
        project_id=1,
        assignee_id=2,
        title="Finalize UI Kit Components",
        priority="medium",
        status="todo",
        sprint_id=sprint1.id,
        story_points=8,
        due_date=date(2026, 10, 24),
        created_at=datetime(2026, 4, 29, 3, 43, 57, 995095),
        updated_at=datetime(2026, 4, 29, 3, 43, 57, 995095),
    ),
    Task(
        id=3,
        project_id=1,
        assignee_id=3,
        title="Database Indexing Review",
        priority="low",
        status="todo",
        sprint_id=sprint1.id,
        story_points=5,
        due_date=date(2026, 10, 26),
        created_at=datetime(2026, 4, 29, 3, 43, 57, 995095),
        updated_at=datetime(2026, 4, 29, 3, 43, 57, 995095),
    ),
    Task(
        id=4,
        project_id=1,
        assignee_id=2,
        title="Create Landing Page",
        priority="high",
        status="done",
        sprint_id=sprint1.id,
        story_points=4,
        due_date=date(2026, 10, 24),
        created_at=datetime(2026, 5, 4, 9, 56, 59),
        updated_at=datetime(2026, 5, 4, 9, 56, 59),
    ),
    Task(
        id=5,
        project_id=1,
        assignee_id=3,
        title="Create dashboard",
        priority="high",
        status="done",
        sprint_id=sprint2.id,
        story_points=4,
        due_date=date(2026, 10, 24),
        created_at=datetime(2026, 5, 4, 9, 57, 13),
        updated_at=datetime(2026, 5, 4, 9, 57, 13),
    ),
    Task(
        id=6,
        project_id=1,
        assignee_id=2,
        title="Implement API Integration",
        priority="medium",
        status="in_progress",
        sprint_id=sprint2.id,
        story_points=5,
        due_date=date(2026, 10, 25),
        created_at=datetime(2026, 5, 4, 9, 59, 1),
        updated_at=datetime(2026, 5, 4, 9, 59, 1),
    ),
    Task(
        id=7,
        project_id=3,
        assignee_id=1,
        title="Design Database Schema",
        priority="high",
        status="done",
        sprint_id=sprint2.id,
        story_points=4,
        due_date=date(2026, 10, 26),
        created_at=datetime(2026, 5, 4, 10, 2, 52),
        updated_at=datetime(2026, 5, 4, 10, 2, 52),
    ),
    Task(
        id=8,
        project_id=3,
        assignee_id=3,
        title="Build API Endpoints",
        priority="medium",
        status="in_progress",
        sprint_id=sprint2.id,
        story_points=5,
        due_date=date(2026, 10, 27),
        created_at=datetime(2026, 5, 4, 10, 3, 3),
        updated_at=datetime(2026, 5, 4, 10, 3, 3),
    ),
    Task(
        id=9,
        project_id=3,
        assignee_id=1,
        title="Frontend Integration",
        priority="medium",
        status="in_progress",
        sprint_id=sprint2.id,
        due_date=date(2026, 10, 28),
        created_at=datetime(2026, 5, 4, 10, 3, 20),
        updated_at=datetime(2026, 5, 4, 10, 3, 20),
    ),
    Task(
        id=10,
        project_id=3,
        assignee_id=1,
        title="Add unit tests",
        priority="medium",
        status="blocker",
        sprint_id=sprint1.id,
        due_date=date(2026, 10, 28),
        created_at=datetime(2026, 5, 4, 10, 3, 20),
        updated_at=datetime(2026, 5, 4, 10, 3, 20),
    )
    ]

    db.session.add_all(tasks)
    db.session.commit()

    print("Tasks seeded successfully.")

    # -------------------------
    # Create sample sprint health check-ins
    # -------------------------

    # These check-ins give the sprint health page realistic demo data.
    checkins = [
        SprintCheckIn(
            sprint_id=sprint1.id,
            user_id=user1.id,
            checkin_date=date.today(),
            confidence_level=4,
            workload_level=3,
            blockers="",
            needs_help=False,
        ),
        SprintCheckIn(
            sprint_id=sprint1.id,
            user_id=user2.id,
            checkin_date=date.today(),
            confidence_level=3,
            workload_level=4,
            blockers="Waiting for final API response examples.",
            needs_help=True,
        ),
        SprintCheckIn(
            sprint_id=sprint1.id,
            user_id=user3.id,
            checkin_date=date.today(),
            confidence_level=2,
            workload_level=5,
            blockers="Database indexing review is taking longer than expected.",
            needs_help=True,
        ),
        SprintCheckIn(
            sprint_id=sprint1.id,
            user_id=user4.id,
            checkin_date=date.today(),
            confidence_level=4,
            workload_level=2,
            blockers="",
            needs_help=False,
        ),
    ]

    db.session.add_all(checkins)
    db.session.commit()

    print("Sprint health check-ins seeded successfully.")

    # -------------------------
    # Create projects-user relationships
    # -------------------------

    project_user_data = [
        {"project_id": 1, "user_id": 1, "assigned_at": datetime(2026, 5, 4, 6, 59, 36, 74425)},
        {"project_id": 1, "user_id": 2, "assigned_at": datetime(2026, 5, 4, 6, 59, 36, 74432)},
        {"project_id": 1, "user_id": 3, "assigned_at": datetime(2026, 5, 4, 7, 0, 28, 909741)},
        {"project_id": 4, "user_id": 2, "assigned_at": datetime(2026, 5, 4, 9, 4, 14, 499581)},
        {"project_id": 6, "user_id": 3, "assigned_at": datetime(2026, 5, 4, 9, 15, 13, 581862)},
        {"project_id": 3, "user_id": 1, "assigned_at": datetime(2026, 5, 4, 9, 19, 53, 233734)},
        {"project_id": 3, "user_id": 3, "assigned_at": datetime(2026, 5, 4, 9, 19, 53, 233749)},
        {"project_id": 2, "user_id": 1, "assigned_at": datetime(2026, 5, 4, 9, 20, 9, 466330)},
    ]

    # Insert into association table
    db.session.execute(project_users.insert(), project_user_data)
    db.session.commit()

    print("Project-user assignments seeded successfully.")
