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
    """Товар в каталоге. Привязан к категории через ForeignKey."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,     # при удалении категории удаляются её товары
        related_name='products',      # category.products.all() — все товары категории
        verbose_name='Категория',
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

    def __str__(self):
        return self.name


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
