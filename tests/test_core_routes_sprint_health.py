import unittest
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Project, Sprint, SprintCheckIn, User


class CoreRoutesSprintHealthTestCase(unittest.TestCase):
    """Backend route tests for protected pages and sprint health check-ins."""

    def setUp(self):
        """Create a fresh Flask app, database, user, project, and active sprint."""
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            user = User(
                full_name="Route Test User",
                email="route@test.com",
                password_hash=generate_password_hash("password123"),
            )
            project = Project(
                name="Route Test Project",
                description="Project used by backend route tests.",
                status="active",
                health_status="healthy",
            )
            db.session.add_all([user, project])
            db.session.commit()

            sprint = Sprint(
                project_id=project.id,
                name="Route Test Sprint",
                goal="Keep route tests realistic.",
                status="active",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=14),
                total_story_points=20,
                completed_story_points=5,
                velocity_points=5,
            )
            db.session.add(sprint)
            db.session.commit()

            self.user_id = user.id
            self.sprint_id = sprint.id

    def tearDown(self):
        """Clear the database session and remove test tables after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        """Log in the seeded user through the Flask test client."""
        return self.client.post("/auth", data={
            "form_type": "login",
            "email": "route@test.com",
            "password": "password123",
        })

    def test_protected_pages_redirect_when_logged_out(self):
        """Protected pages should redirect unauthenticated users to login."""
        protected_paths = [
            "/dashboard",
            "/sprints",
            "/project",
            "/backlog",
            "/analytics",
        ]

        for path in protected_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/auth", response.headers["Location"])

    def test_dashboard_loads_for_logged_in_user(self):
        """The dashboard should load successfully for an authenticated user."""
        self.login()
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back", response.data)

    def test_sprints_page_loads_for_logged_in_user(self):
        """The sprints page should show the active sprint to a logged-in user."""
        self.login()
        response = self.client.get("/sprints")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Route Test Sprint", response.data)

    def test_sprint_health_checkin_can_be_saved(self):
        """Posting the sprint health form should create a check-in row."""
        self.login()
        response = self.client.post(f"/sprints/{self.sprint_id}/check-in", data={
            "confidence_level": "4",
            "workload_level": "3",
            "blockers": "Waiting for API details",
            "needs_help": "on",
        })

        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            checkin = SprintCheckIn.query.one()
            self.assertEqual(checkin.sprint_id, self.sprint_id)
            self.assertEqual(checkin.user_id, self.user_id)
            self.assertEqual(checkin.confidence_level, 4)
            self.assertEqual(checkin.workload_level, 3)
            self.assertEqual(checkin.blockers, "Waiting for API details")
            self.assertTrue(checkin.needs_help)

    def test_same_day_sprint_health_checkin_updates_existing_row(self):
        """A second same-day check-in should update the existing row."""
        self.login()
        first_payload = {
            "confidence_level": "2",
            "workload_level": "5",
            "blockers": "Initial blocker",
        }
        updated_payload = {
            "confidence_level": "5",
            "workload_level": "2",
            "blockers": "Resolved blocker",
            "needs_help": "on",
        }

        self.client.post(f"/sprints/{self.sprint_id}/check-in", data=first_payload)
        self.client.post(f"/sprints/{self.sprint_id}/check-in", data=updated_payload)

        with self.app.app_context():
            self.assertEqual(SprintCheckIn.query.count(), 1)
            checkin = SprintCheckIn.query.one()
            self.assertEqual(checkin.confidence_level, 5)
            self.assertEqual(checkin.workload_level, 2)
            self.assertEqual(checkin.blockers, "Resolved blocker")
            self.assertTrue(checkin.needs_help)


if __name__ == "__main__":
    unittest.main()
