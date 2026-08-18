from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class RegisterViewTests(TestCase):

    def test_register_get_renders_form(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_post_creates_user_and_hashes_password(self):
        response = self.client.post(reverse('register'), {
            'name': 'Test User',
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123',
        })
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test User')
        self.assertFalse(user.password == 'StrongPass123')
        self.assertTrue(user.check_password('StrongPass123'))

    def test_register_invalid_data_rerenders_form(self):
        response = self.client.post(reverse('register'), {
            'name': '',
            'username': '',
            'email': 'not-an-email',
            'password': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_duplicate_username_rerenders_form(self):
        User.objects.create_user(username='existing', password='Pass1234')
        response = self.client.post(reverse('register'), {
            'name': 'X',
            'username': 'existing',
            'email': 'x@example.com',
            'password': 'StrongPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertEqual(User.objects.filter(username='existing').count(), 1)


class LoginViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='johndoe', password='Secret123'
        )

    def test_login_success_redirects_to_product_list(self):
        response = self.client.post(reverse('login'), {
            'username': 'johndoe',
            'password': 'Secret123',
        })
        self.assertRedirects(response, reverse('product_list'))

    def test_login_wrong_password_rejected(self):
        response = self.client.post(reverse('login'), {
            'username': 'johndoe',
            'password': 'WrongPass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_get_renders_form(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')


class LogoutViewTests(TestCase):

    def test_logout_redirects_to_login(self):
        self.client.login(username='johndoe', password='Secret123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        # Verify the user is actually logged out
        session_user = self.client.session.get('_auth_user_id')
        self.assertIsNone(session_user)