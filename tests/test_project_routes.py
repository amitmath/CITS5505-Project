import unittest

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Project, User


class ProjectRoutesTestCase(unittest.TestCase):
    """Backend route tests for the project list and project detail flows."""

    def setUp(self):
        """Create a fresh app, database, user, and project fixtures per test."""
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
                full_name="Project Test User",
                email="project@test.com",
                password_hash=generate_password_hash("password123"),
            )
            active_project = Project(
                name="Alpha Project",
                description="First active project.",
                status="active",
                health_status="healthy",
            )
            archived_project = Project(
                name="Archived Project",
                description="Should not appear in the active project list.",
                status="archived",
                health_status="healthy",
            )
            db.session.add_all([user, active_project, archived_project])
            db.session.commit()

            self.user_id = user.id
            self.project_id = active_project.id
            self.archived_id = archived_project.id

    def tearDown(self):
        """Remove test database tables after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        """Log in the seeded user through the Flask test client."""
        return self.client.post("/auth", data={
            "form_type": "login",
            "email": "project@test.com",
            "password": "password123",
        })


    # ------------------------------------------------------------------ #
    # Project list  /project
    # ------------------------------------------------------------------ #

    def test_project_list_redirects_when_logged_out(self):
        """Unauthenticated GET /project should redirect to the login page."""
        response = self.client.get("/project")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth", response.headers["Location"])

    def test_project_list_loads_for_logged_in_user(self):
        """GET /project should render the active project for a logged-in user."""
        self.login()
        response = self.client.get("/project")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alpha Project", response.data)

    def test_project_list_excludes_non_active_projects(self):
        """GET /project should not show projects whose status is not 'active'."""
        self.login()
        response = self.client.get("/project")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Archived Project", response.data)

    def test_project_search_redirects_to_detail_on_single_match(self):
        """A search that matches exactly one project should redirect to its detail page."""
        self.login()
        response = self.client.get("/project?search=Alpha")
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/projects/{self.project_id}", response.headers["Location"])

    def test_project_search_returns_200_when_no_match(self):
        """A search with no matching projects should return the list page with no results."""
        self.login()
        response = self.client.get("/project?search=Nonexistent")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Alpha Project", response.data)


if __name__ == "__main__":
    unittest.main()
