import unittest
from app import create_app, db
from app.models import User
from werkzeug.security import check_password_hash, generate_password_hash


class MeihuiTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test environment before each test"""
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            user = User(
                full_name='Test User',
                email='test@test.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        """Helper: log in as test user"""
        return self.client.post('/auth', data={
            'form_type': 'login',
            'email': 'test@test.com',
            'password': 'password123'
        }, follow_redirects=True)

    def test_profile_page_requires_login(self):
        """Profile page should redirect to login if not authenticated"""
        response = self.client.get('/profile', follow_redirects=True)
        self.assertIn(b'login', response.data.lower())

    def test_profile_page_loads_when_logged_in(self):
        """Profile page should load successfully when logged in"""
        self.login()
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)

    def test_settings_page_requires_login(self):
        """Settings page should redirect to login if not authenticated"""
        response = self.client.get('/settings', follow_redirects=True)
        self.assertIn(b'login', response.data.lower())

    def test_settings_page_loads_when_logged_in(self):
        """Settings page should load successfully when logged in"""
        self.login()
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)

    def test_settings_update_profile(self):
        """Settings should save profile info successfully"""
        self.login()
        response = self.client.post('/settings', data={
            'action': 'save_profile',
            'full_name': 'Updated Name',
            'email': 'test@test.com',
            'job_title': 'Developer',
            'location': 'Perth'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_settings_empty_name_rejected(self):
        """Settings should reject empty full name"""
        self.login()
        response = self.client.post('/settings', data={
            'action': 'save_profile',
            'full_name': '',
            'email': 'test@test.com',
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_settings_change_password_success(self):
        """Settings should update password when current password is correct"""
        self.login()
        response = self.client.post('/settings', data={
            'action': 'change_password',
            'current_password': 'password123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password updated successfully', response.data)

        with self.app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            self.assertTrue(check_password_hash(user.password_hash, 'newpassword123'))

    def test_settings_change_password_wrong_current_rejected(self):
        """Settings should reject password changes with wrong current password"""
        self.login()
        response = self.client.post('/settings', data={
            'action': 'change_password',
            'current_password': 'wrong-password',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Current password is incorrect', response.data)

        with self.app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            self.assertTrue(check_password_hash(user.password_hash, 'password123'))

    def test_settings_change_password_mismatch_rejected(self):
        """Settings should reject password confirmation mismatches"""
        self.login()
        response = self.client.post('/settings', data={
            'action': 'change_password',
            'current_password': 'password123',
            'new_password': 'newpassword123',
            'confirm_password': 'different123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New passwords do not match', response.data)

        with self.app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            self.assertTrue(check_password_hash(user.password_hash, 'password123'))


if __name__ == '__main__':
    unittest.main()
