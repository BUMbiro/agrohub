from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя.

    - Авторизация по email (USERNAME_FIELD = 'email').
    - Дополнительные поля: аватар, номер телефона, страна.
    """

    email = models.EmailField(
        unique=True,
        verbose_name='Email',
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Номер телефона',
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Страна',
    )

    # Авторизация по email, а не по username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []            # email уже есть, username необязателен

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
