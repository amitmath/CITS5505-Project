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


if __name__ == "__main__":
    unittest.main()
