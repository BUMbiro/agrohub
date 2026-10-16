from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail

from .models import User


class RegistrationTests(TestCase):
    """Тесты регистрации пользователя."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')

    def test_registration_page_opens(self):
        """Страница регистрации открывается."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_user_registers_successfully(self):
        """Пользователь успешно регистрируется и логинится."""
        response = self.client.post(self.register_url, {
            'email': 'newuser@example.com',
            'password1': 'StrongPass2026!',
            'password2': 'StrongPass2026!',
        })
        # После регистрации — редирект на главную
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

        # Пользователь залогинен
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_registration_sends_welcome_email(self):
        """После регистрации отправляется приветственное письмо."""
        self.client.post(self.register_url, {
            'email': 'newuser@example.com',
            'password1': 'StrongPass2026!',
            'password2': 'StrongPass2026!',
        })
        # В outbox ровно 1 письмо
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('newuser@example.com', mail.outbox[0].to)

    def test_registration_duplicate_email_fails(self):
        """Регистрация с занятым email не проходит."""
        User.objects.create_user(email='exist@example.com', password='StrongPass2026!')

        response = self.client.post(self.register_url, {
            'email': 'exist@example.com',
            'password1': 'StrongPass2026!',
            'password2': 'StrongPass2026!',
        })
        # Форма с ошибкой (не редирект)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'уже зарегистрирован')

    def test_registration_password_mismatch_fails(self):
        """Разные пароли не проходят."""
        response = self.client.post(self.register_url, {
            'email': 'newuser@example.com',
            'password1': 'StrongPass2026!',
            'password2': 'DifferentPass2026!',
        })
        self.assertEqual(response.status_code, 200)
        # Пользователь не создан
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())


class LoginTests(TestCase):
    """Тесты входа."""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('users:login')
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass2026!',
        )

    def test_login_with_valid_credentials(self):
        """Вход с правильными данными работает."""
        response = self.client.post(self.login_url, {
            'email': 'user@example.com',
            'password': 'StrongPass2026!',
        })
        self.assertEqual(response.status_code, 302)  # редирект после логина

    def test_login_with_wrong_password_fails(self):
        """Неверный пароль — ошибка."""
        response = self.client.post(self.login_url, {
            'email': 'user@example.com',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный email или пароль')

    def test_login_with_wrong_email_fails(self):
        """Несуществующий email — ошибка."""
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com',
            'password': 'StrongPass2026!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный email или пароль')


class ProfileTests(TestCase):
    """Тесты редактирования профиля."""

    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('users:profile')
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass2026!',
        )

    def test_profile_requires_login(self):
        """Анонимный не может открыть профиль — редирект на логин."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_profile_opens_for_authenticated(self):
        """Авторизованный открывает профиль."""
        self.client.login(username='user@example.com', password='StrongPass2026!')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_update_saves_data(self):
        """Профиль сохраняет изменения."""
        self.client.login(username='user@example.com', password='StrongPass2026!')
        response = self.client.post(self.profile_url, {
            'email': 'user@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'phone_number': '+7 (999) 123-45-67',
            'country': 'Россия',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Иван')
        self.assertEqual(self.user.country, 'Россия')


class LogoutTests(TestCase):
    """Тесты выхода."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass2026!',
        )

    def test_logout_redirects_to_home(self):
        """Выход редиректит на главную."""
        self.client.login(username='user@example.com', password='StrongPass2026!')
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)
