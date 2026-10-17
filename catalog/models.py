from django.conf import settings
from django.db import models


class Category(models.Model):
    """Категория товаров (например, «Семена», «Удобрения» и т.п.)."""

    name = models.CharField(
        max_length=100,
        verbose_name='Наименование',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='URL-идентификатор',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']  # сортировка по имени по умолчанию

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар в каталоге.

    Привязан к категории и к пользователю-владельцу (owner).
    Имеет статус публикации (is_published) и кастомное право
    can_unpublish_product для модераторов.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,     # при удалении категории удаляются её товары
        related_name='products',      # category.products.all() — все товары категории
        verbose_name='Категория',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,    # если юзера удалили — товар остаётся, owner=None
        null=True,                    # null=True, чтобы миграция не падала на существующих товарах
        blank=True,
        related_name='products',      # user.products.all() — товары пользователя
        verbose_name='Владелец',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Наименование',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='URL-идентификатор',
    )
    description = models.TextField(
        verbose_name='Описание',
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена',
    )
    unit = models.CharField(
        max_length=20,
        default='шт.',
        blank=True,
        verbose_name='Единица измерения',
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Изображение',
    )
    in_stock = models.BooleanField(
        default=True,
        verbose_name='В наличии',
    )
    is_published = models.BooleanField(
        default=False,                # по критерию: default = «не опубликован»
        verbose_name='Опубликован',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,            # ставится один раз при создании
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,                # обновляется при каждом save()
        verbose_name='Дата последнего изменения',
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['-created_at']    # новые сверху
        permissions = [
            # Кастомное право для модераторов: снимать товар с публикации
            ('can_unpublish_product', 'Может отменять публикацию продукта'),
        ]

    def __str__(self):
        return self.name

    # --------------------------------------------------------
    # Хелперы прав доступа
    # --------------------------------------------------------

    def can_be_managed_by(self, user):
        """Может ли пользователь редактировать/удалять этот товар.

        Доступ разрешён:
        - владельцу товара;
        - модератору (у кого есть право can_unpublish_product);
        - суперпользователю.
        """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if self.owner_id == user.id:                  # владелец товара
            return True
        return user.has_perm('catalog.can_unpublish_product')  # модератор

    def can_be_unpublished_by(self, user):
        """Может ли пользователь менять статус публикации товара.

        Только модератор или суперюзер. Владелец сам публиковать не может —
        в этом и смысл ручной модерации.
        """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.has_perm('catalog.can_unpublish_product')


class News(models.Model):
    """Новости фермеров на главной странице."""

    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок',
    )
    content = models.TextField(
        verbose_name='Содержание',
    )
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата',
    )
    image = models.ImageField(
        upload_to='news/',
        blank=True,
        null=True,
        verbose_name='Изображение',
    )

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-date']

    def __str__(self):
        return self.title


class Contact(models.Model):
    """Контактные данные магазина (для страницы контактов)."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название организации',
    )
    address = models.CharField(
        max_length=200,
        verbose_name='Адрес',
    )
    phone = models.CharField(
        max_length=30,
        verbose_name='Телефон',
    )
    email = models.EmailField(
        verbose_name='Email',
    )

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return self.name
