import threading
import unittest
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.pool import StaticPool
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import create_app, db
from app.models import Project, Sprint, Task, User


class SeleniumCoreFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        cls.server.shutdown()
        cls.server_thread.join(timeout=5)
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()

            self.user = User(
                full_name="Selenium Core User",
                email="selenium-core@test.com",
                password_hash=generate_password_hash("password123"),
            )
            self.project = Project(
                name="Selenium Demo Project",
                description="Project used by Selenium flow tests.",
                status="active",
                health_status="healthy",
            )
            db.session.add_all([self.user, self.project])
            db.session.commit()

            self.sprint = Sprint(
                project_id=self.project.id,
                name="Selenium Active Sprint",
                goal="Check the main browser workflow.",
                status="active",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=10),
                total_story_points=20,
                completed_story_points=5,
                velocity_points=5,
            )
            db.session.add(self.sprint)
            db.session.commit()

            task = Task(
                project_id=self.project.id,
                sprint_id=self.sprint.id,
                assignee_id=self.user.id,
                created_by=self.user.id,
                title="Selenium assigned task",
                status="in_progress",
                story_points=3,
                due_date=date.today() + timedelta(days=2),
            )
            db.session.add(task)
            db.session.commit()

            self.user_id = self.user.id
            self.sprint_id = self.sprint.id

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1440,1000")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        self.driver.get(f"{self.base_url}/auth?mode=login")
        login_form = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form[data-auth-form='login']"))
        )
        login_form.find_element(By.NAME, "email").send_keys("selenium-core@test.com")
        login_form.find_element(By.NAME, "password").send_keys("password123")
        login_form.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait.until(EC.url_contains("/dashboard"))

    def test_protected_dashboard_redirects_to_login(self):
        self.driver.get(f"{self.base_url}/dashboard")

        self.wait.until(EC.url_contains("/auth"))
        self.assertIn("mode=login", self.driver.current_url)

    def test_login_opens_dashboard(self):
        self.login()

        self.assertIn("/dashboard", self.driver.current_url)
        self.assertIn("Welcome back, Selenium Core User", self.driver.page_source)

    def test_dashboard_shows_live_project_and_task_data(self):
        self.login()

        self.assertIn("Selenium Demo Project", self.driver.page_source)
        self.assertIn("Selenium assigned task", self.driver.page_source)
        self.assertIn("Selenium Active Sprint", self.driver.page_source)


if __name__ == "__main__":
    unittest.main()
