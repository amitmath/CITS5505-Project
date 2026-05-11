import unittest
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash



class SeleniumTestCase(unittest.TestCase):

    def setUp(self):
        """Start Flask server and browser before each test"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_selenium.db'
        self.app.config['WTF_CSRF_ENABLED'] = False

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            user = User(
                full_name='Selenium User',
                email='selenium@test.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
            db.session.commit()

        self.server_thread = threading.Thread(
            target=self.app.run,
            kwargs={'port': 5001, 'use_reloader': False}
        )
        self.server_thread.daemon = True
        self.server_thread.start()

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.base_url = 'http://127.0.0.1:5001'

    def tearDown(self):
        """Close browser after each test"""
        self.driver.quit()
        with self.app.app_context():
            db.drop_all()

    def login(self):
        """Helper: log in via browser"""
        self.driver.get(f'{self.base_url}/auth')
        self.driver.find_element(By.NAME, 'email').send_keys('selenium@test.com')
        self.driver.find_element(By.NAME, 'password').send_keys('password123')
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]").click()
        time.sleep(2)

    def test_landing_page_loads(self):
        """Landing page should load successfully"""
        self.driver.get(self.base_url)
        self.assertIn('Agile', self.driver.title)

    def test_login_page_loads(self):
        """Login page should load successfully"""
        self.driver.get(f'{self.base_url}/auth')
        self.assertIn('login', self.driver.page_source.lower())

    def test_profile_page_accessible_after_login(self):
        """Profile page should redirect to login if not logged in"""
        self.driver.get(f'{self.base_url}/profile')
        self.assertIn('auth', self.driver.current_url)

    def test_settings_page_accessible_after_login(self):
        """Settings page should redirect to login if not logged in"""
        self.driver.get(f'{self.base_url}/settings')
        self.assertIn('auth', self.driver.current_url)

    def test_logout_redirects_to_login(self):
        """Logout should redirect to login page"""
        self.login()
        self.driver.get(f'{self.base_url}/logout')
        self.assertIn('auth', self.driver.current_url)


if __name__ == '__main__':
    unittest.main()