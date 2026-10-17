from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели User.

    Главное отличие от стандартного: создаёт пользователей по email,
    а не по username. Username генерируется автоматически из email,
    если не передан явно.
    """

    def _generate_unique_username(self, email):
        """Генерирует уникальный username из email.

        Берём часть до @, обрезаем до 150 символов (max_length поля).
        Если такой username уже занят — добавляем суффикс -1, -2, ...
        """
        base = email.split('@')[0][:150] or 'user'
        username = base
        counter = 1

        # Пока username занят — увеличиваем счётчик
        while self.model.objects.filter(username=username).exists():
            # Оставляем место под суффикс, чтобы не выйти за 150 символов
            suffix = f'-{counter}'
            username = f'{base[:150 - len(suffix)]}{suffix}'
            counter += 1

        return username

    def create_user(self, email, password=None, **extra_fields):
        """Создаёт обычного пользователя по email и паролю."""
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)

        # Если username не передан — генерим из email.
        # Иначе Django попытается сохранить пустую строку и упадёт на unique-констрейнте.
        if not extra_fields.get('username'):
            extra_fields['username'] = self._generate_unique_username(email)

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
