from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели User.

    Главное отличие от стандартного: создаёт пользователей по email,
    а не по username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Создаёт обычного пользователя по email и паролю."""
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создаёт суперюзера по email и паролю."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Суперюзер должен иметь is_staff=True')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Суперюзер должен иметь is_superuser=True')

        return self.create_user(email, password, **extra_fields)
