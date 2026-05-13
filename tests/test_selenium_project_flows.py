import threading
import unittest
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from sqlalchemy.pool import StaticPool
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import create_app, db
from app.models import Project, Task, User


class SeleniumProjectFlowTestCase(unittest.TestCase):
    """Selenium coverage for the project list and project detail flows."""

    @classmethod
    def setUpClass(cls):
        """Start a live Flask server backed by a shared in-memory test database."""
        cls.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
            "WTF_CSRF_ENABLED": False,
        })
        cls.server = make_server("127.0.0.1", 0, cls.app)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        """Stop the live server and release database connections after the suite."""
        cls.server.shutdown()
        cls.server_thread.join(timeout=5)
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        """Create fresh browser, user, project, and task fixtures per test."""
        with self.app.app_context():
            db.drop_all()
            db.create_all()

            self.user = User(
                full_name="Selenium Project User",
                email="selenium-project@test.com",
                password_hash=generate_password_hash("password123"),
            )
            self.active_project = Project(
                name="Selenium Active Project",
                description="Active project for Selenium tests.",
                status="active",
                health_status="healthy",
            )
            self.archived_project = Project(
                name="Selenium Archived Project",
                description="Should not appear in project list.",
                status="archived",
                health_status="healthy",
            )
            db.session.add_all([self.user, self.active_project, self.archived_project])
            db.session.commit()

            task = Task(
                project_id=self.active_project.id,
                title="Selenium Project Task",
                status="in_progress",
                created_by=self.user.id,
            )
            db.session.add(task)
            db.session.commit()

            self.user_id = self.user.id
            self.project_id = self.active_project.id

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1440,1000")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        """Close the browser and reset database state after each test."""
        self.driver.quit()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        """Log the seeded user in through the browser UI."""
        self.driver.get(f"{self.base_url}/auth?mode=login")
        login_form = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form[data-auth-form='login']"))
        )
        login_form.find_element(By.NAME, "email").send_keys("selenium-project@test.com")
        login_form.find_element(By.NAME, "password").send_keys("password123")
        login_form.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait.until(EC.url_contains("/dashboard"))

    # ------------------------------------------------------------------ #
    # Project list  /project
    # ------------------------------------------------------------------ #

    def test_project_list_redirects_when_logged_out(self):
        """Logged-out users should be redirected from the project list to login."""
        self.driver.get(f"{self.base_url}/project")
        self.wait.until(EC.url_contains("/auth"))
        self.assertIn("mode=login", self.driver.current_url)

    def test_project_list_shows_active_projects(self):
        """The project list should display cards for all active projects."""
        self.login()
        self.driver.get(f"{self.base_url}/project")
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Selenium Active Project"))
        self.assertIn("Selenium Active Project", self.driver.page_source)

    def test_project_list_does_not_show_archived_projects(self):
        """Archived projects should not appear on the project list page."""
        self.login()
        self.driver.get(f"{self.base_url}/project")
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Active Projects"))
        self.assertNotIn("Selenium Archived Project", self.driver.page_source)

    def test_create_project_via_modal(self):
        """Opening the New Project modal and submitting should add the project to the list."""
        self.login()
        self.driver.get(f"{self.base_url}/project")

        open_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "openProjectModal")))
        self.driver.execute_script("arguments[0].click();", open_btn)

        name_input = self.wait.until(EC.visibility_of_element_located((By.ID, "projectName")))
        name_input.send_keys("Browser Created Project")
        self.driver.find_element(By.ID, "projectDescription").send_keys("Created from Selenium test.")
        Select(self.driver.find_element(By.ID, "projectStatus")).select_by_value("active")

        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "#projectModal button[type='submit']")
        self.driver.execute_script("arguments[0].click();", submit_btn)

        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Browser Created Project"))
        self.assertIn("Browser Created Project", self.driver.page_source)

        with self.app.app_context():
            project = Project.query.filter_by(name="Browser Created Project").first()
            self.assertIsNotNone(project)
            self.assertEqual(project.description, "Created from Selenium test.")
            self.assertEqual(project.status, "active")

    def test_clicking_project_card_navigates_to_detail(self):
        """Clicking a project card on the list should navigate to its detail page."""
        self.login()
        self.driver.get(f"{self.base_url}/project")

        card_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//a[contains(@href, '/projects/{self.project_id}')]")
            )
        )
        card_link.click()
        self.wait.until(EC.url_contains(f"/projects/{self.project_id}"))
        self.assertIn("Selenium Active Project", self.driver.page_source)

    # ------------------------------------------------------------------ #
    # Project detail  /projects/<id>
    # ------------------------------------------------------------------ #

    def test_project_detail_loads(self):
        """The project detail page should render the project name and overview section."""
        self.login()
        self.driver.get(f"{self.base_url}/projects/{self.project_id}")

        self.wait.until(EC.url_contains(f"/projects/{self.project_id}"))
        self.assertIn("Selenium Active Project", self.driver.page_source)
        self.assertIn("Active project for Selenium tests.", self.driver.page_source)
        self.assertIn("Project Overview", self.driver.page_source)

    def test_project_detail_shows_task(self):
        """Tasks belonging to the project should appear on the detail page."""
        self.login()
        self.driver.get(f"{self.base_url}/projects/{self.project_id}")

        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Selenium Project Task"))
        self.assertIn("Selenium Project Task", self.driver.page_source)

    def test_project_detail_edit_modal_saves_changes(self):
        """Submitting the edit modal should persist the updated name and description."""
        self.login()
        self.driver.get(f"{self.base_url}/projects/{self.project_id}")

        open_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "openEditProjectModal")))
        self.driver.execute_script("arguments[0].click();", open_btn)

        name_input = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#editProjectModal input[name='name']")
        ))
        name_input.clear()
        name_input.send_keys("Renamed Selenium Project")
        desc = self.driver.find_element(By.CSS_SELECTOR, "#editProjectModal textarea[name='description']")
        desc.clear()
        desc.send_keys("Updated description.")
        Select(self.driver.find_element(
            By.CSS_SELECTOR, "#editProjectModal select[name='health_status']"
        )).select_by_value("at-risk")

        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "#editProjectModal button[type='submit']")
        self.driver.execute_script("arguments[0].click();", submit_btn)

        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Renamed Selenium Project"))
        self.assertIn("Renamed Selenium Project", self.driver.page_source)

        with self.app.app_context():
            project = db.session.get(Project, self.project_id)
            self.assertEqual(project.name, "Renamed Selenium Project")
            self.assertEqual(project.description, "Updated description.")
            self.assertEqual(project.health_status, "at-risk")

    def test_project_detail_assign_users_modal_saves_assignment(self):
        """Checking a user in the assign-users modal and saving should add them to the team."""
        self.login()
        self.driver.get(f"{self.base_url}/projects/{self.project_id}")

        open_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "openAssignUsersModal")))
        self.driver.execute_script("arguments[0].click();", open_btn)

        user_checkbox = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"#assignUsersModal input[name='user_ids'][value='{self.user_id}']")
        ))
        if not user_checkbox.is_selected():
            self.driver.execute_script("arguments[0].click();", user_checkbox)

        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "#assignUsersModal button[type='submit']")
        self.driver.execute_script("arguments[0].click();", submit_btn)

        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Selenium Project User"))
        self.assertIn("Selenium Project User", self.driver.page_source)

        with self.app.app_context():
            project = db.session.get(Project, self.project_id)
            assigned_ids = [u.id for u in project.assigned_users]
            self.assertIn(self.user_id, assigned_ids)

    def test_project_detail_delete_project_removes_and_redirects(self):
        """Confirming the delete modal should remove the project and redirect to the project list."""
        self.login()
        self.driver.get(f"{self.base_url}/projects/{self.project_id}")

        open_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "openDeleteProjectModal")))
        self.driver.execute_script("arguments[0].click();", open_btn)

        delete_submit = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#deleteProjectModal .project-delete-submit-btn")
        ))
        self.driver.execute_script("arguments[0].click();", delete_submit)

        self.wait.until(EC.url_contains("/project"))
        self.assertNotIn(f"/projects/{self.project_id}", self.driver.current_url)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Project, self.project_id))


if __name__ == "__main__":
    unittest.main()
