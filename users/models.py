from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Кастомная модель пользователя.

    Вход по email (USERNAME_FIELD), username генерируется автоматически.
    Доп. поля: avatar, phone_number, country.
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
        verbose_name='Телефон',
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Страна',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    # --------------------------------------------------------
    # Хелперы для шаблонов (property без аргументов)
    # --------------------------------------------------------

    @property
    def is_moderator(self):
        """Модератор продуктов: имеет право can_unpublish_product.

        Используется в шаблонах как {% if user.is_moderator %}.
        В шаблонах нельзя вызывать user.has_perm('catalog.x') — Django
        не умеет передавать аргументы. Поэтому оборачиваем в property.
        """
        return self.has_perm('catalog.can_unpublish_product')

    @property
    def is_content_manager(self):
        """Контент-менеджер блога: может управлять статьями.

        Права появятся после группы «Контент-менеджер» (доп. задание).
        Пока для обычных юзеров вернёт False.
        """
        return (
            self.has_perm('blog.change_blogpost')
            or self.has_perm('blog.add_blogpost')
            or self.has_perm('blog.delete_blogpost')
        )
