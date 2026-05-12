import unittest

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Project, Task, User


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


    # ------------------------------------------------------------------ #
    # Create project  POST /projects/create
    # ------------------------------------------------------------------ #

    def test_create_project_redirects_when_logged_out(self):
        """Unauthenticated POST /projects/create should redirect to the login page."""
        response = self.client.post("/projects/create", data={
            "name": "Should Not Save",
            "status": "active",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth", response.headers["Location"])

    def test_create_project_saves_to_database(self):
        """A valid POST /projects/create should persist the new project."""
        self.login()
        response = self.client.post("/projects/create", data={
            "name": "New Project",
            "description": "Created by the route test.",
            "status": "active",
        })
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            project = Project.query.filter_by(name="New Project").first()
            self.assertIsNotNone(project)
            self.assertEqual(project.description, "Created by the route test.")
            self.assertEqual(project.status, "active")
            self.assertEqual(project.health_status, "healthy")

    def test_create_project_requires_name(self):
        """POST /projects/create with an empty name should not create a record."""
        self.login()
        self.client.post("/projects/create", data={
            "name": "",
            "description": "Missing name.",
            "status": "active",
        })

        with self.app.app_context():
            # Only the two projects from setUp should exist.
            self.assertEqual(Project.query.count(), 2)

    # ------------------------------------------------------------------ #
    # Project detail  GET /projects/<id>
    # ------------------------------------------------------------------ #

    def test_project_detail_redirects_when_logged_out(self):
        """Unauthenticated GET /projects/<id> should redirect to the login page."""
        response = self.client.get(f"/projects/{self.project_id}")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth", response.headers["Location"])

    def test_project_detail_loads_for_logged_in_user(self):
        """GET /projects/<id> should render the project detail page."""
        self.login()
        response = self.client.get(f"/projects/{self.project_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alpha Project", response.data)

    def test_project_detail_returns_404_for_unknown_id(self):
        """GET /projects/<id> for a non-existent project should return 404."""
        self.login()
        response = self.client.get("/projects/9999")
        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------------ #
    # Edit project  POST /projects/<id>/edit
    # ------------------------------------------------------------------ #

    def test_edit_project_updates_database(self):
        """A valid POST /projects/<id>/edit should persist all changed fields."""
        self.login()
        response = self.client.post(f"/projects/{self.project_id}/edit", data={
            "name": "Renamed Project",
            "description": "Updated description.",
            "status": "active",
            "health_status": "at_risk",
        })
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            project = db.session.get(Project, self.project_id)
            self.assertEqual(project.name, "Renamed Project")
            self.assertEqual(project.description, "Updated description.")
            self.assertEqual(project.health_status, "at_risk")

    def test_edit_project_requires_name(self):
        """POST /projects/<id>/edit with an empty name should leave the project unchanged."""
        self.login()
        self.client.post(f"/projects/{self.project_id}/edit", data={
            "name": "",
            "description": "Attempted update.",
            "status": "active",
            "health_status": "healthy",
        })

        with self.app.app_context():
            project = db.session.get(Project, self.project_id)
            self.assertEqual(project.name, "Alpha Project")

    # ------------------------------------------------------------------ #
    # Delete project  POST /projects/<id>/delete
    # ------------------------------------------------------------------ #

    def test_delete_project_removes_from_database(self):
        """POST /projects/<id>/delete should remove the project row."""
        self.login()
        response = self.client.post(f"/projects/{self.project_id}/delete")
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Project, self.project_id))

    def test_delete_project_cascades_to_tasks(self):
        """Deleting a project should also remove all tasks that belong to it."""
        with self.app.app_context():
            task = Task(
                project_id=self.project_id,
                title="Cascade Test Task",
                created_by=self.user_id,
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        self.login()
        self.client.post(f"/projects/{self.project_id}/delete")

        with self.app.app_context():
            self.assertIsNone(db.session.get(Task, task_id))

    # ------------------------------------------------------------------ #
    # Assign users  POST /projects/<id>/assign-users
    # ------------------------------------------------------------------ #

    def test_assign_users_to_project(self):
        """POST /projects/<id>/assign-users should link the selected users."""
        self.login()
        response = self.client.post(
            f"/projects/{self.project_id}/assign-users",
            data={"user_ids": [str(self.user_id)]},
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            project = db.session.get(Project, self.project_id)
            assigned_ids = [u.id for u in project.assigned_users]
            self.assertIn(self.user_id, assigned_ids)

    def test_assign_no_users_clears_existing_assignments(self):
        """Submitting an empty user list should remove all existing assignments."""
        self.login()
        self.client.post(
            f"/projects/{self.project_id}/assign-users",
            data={"user_ids": [str(self.user_id)]},
        )
        self.client.post(
            f"/projects/{self.project_id}/assign-users",
            data={},
        )

        with self.app.app_context():
            project = db.session.get(Project, self.project_id)
            self.assertEqual(len(project.assigned_users), 0)


if __name__ == "__main__":
    unittest.main()
