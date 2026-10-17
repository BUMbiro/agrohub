from django.contrib.auth.models import Group, Permission
from django.test import TestCase, Client
from django.urls import reverse

from users.models import User

from .models import Category, Product


class ProductCRUDPermissionsTests(TestCase):
    """Тесты защиты CRUD товаров от анонимов."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Семена',
            slug='semena',
            description='Семена',
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Томат Черри',
            slug='tomat-cherri',
            description='Сладкие томаты',
            price=150,
            unit='упак.',
            is_published=True,   # опубликован, чтобы аноним мог видеть детальную
        )

    def test_anonymous_cannot_create_product(self):
        """Аноним не может открыть форму создания — редирект на логин."""
        response = self.client.get(reverse('catalog:product_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_anonymous_cannot_update_product(self):
        """Аноним не может редактировать товар."""
        response = self.client.get(reverse('catalog:product_update', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_anonymous_cannot_delete_product(self):
        """Аноним не может удалять товар."""
        response = self.client.get(reverse('catalog:product_delete', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_anonymous_can_view_product_list(self):
        """Аноним может смотреть главную."""
        response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_view_product_detail(self):
        """Аноним может смотреть детальную опубликованного товара."""
        response = self.client.get(reverse('catalog:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)


class ProductOwnerTests(TestCase):
    """Тесты привязки товара к владельцу (owner)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@test.ru',
            password='test12345',
        )
        self.category = Category.objects.create(
            name='Семена',
            slug='semena',
        )
        self.client.force_login(self.user)

    def test_owner_is_set_on_create(self):
        """При создании товара owner автоматически = текущий юзер."""
        response = self.client.post(
            reverse('catalog:product_create'),
            data={
                'category': self.category.pk,
                'name': 'Морковь',
                'description': 'Сладкая морковь',
                'price': '100.00',
                'unit': 'кг',
                'in_stock': True,
            },
        )
        # Должен быть редирект на детальную нового товара
        self.assertEqual(response.status_code, 302)

        product = Product.objects.get(name='Морковь')
        self.assertEqual(product.owner, self.user)
        # Новый товар по умолчанию не опубликован
        self.assertFalse(product.is_published)


class ProductModerationTests(TestCase):
    """Тесты прав владельца и модератора на управление товаром."""

    def setUp(self):
        self.client = Client()

        # Владелец товара
        self.owner = User.objects.create_user(
            email='owner@test.ru',
            password='test12345',
        )
        # Другой обычный юзер
        self.other = User.objects.create_user(
            email='other@test.ru',
            password='test12345',
        )
        # Модератор (в группе с правом can_unpublish_product)
        self.moderator = User.objects.create_user(
            email='moder@test.ru',
            password='test12345',
        )
        group = Group.objects.create(name='Модератор продуктов (тест)')
        perm = Permission.objects.get(
            codename='can_unpublish_product',
            content_type__app_label='catalog',
        )
        group.permissions.add(perm)
        self.moderator.groups.add(group)

        self.category = Category.objects.create(name='Семена', slug='semena')
        self.product = Product.objects.create(
            category=self.category,
            owner=self.owner,
            name='Томат Черри',
            slug='tomat-cherri',
            description='Сладкие томаты',
            price=150,
            unit='упак.',
            is_published=True,
        )

    def test_owner_can_update_product(self):
        """Владелец может редактировать свой товар."""
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('catalog:product_update', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_can_delete_product(self):
        """Владелец может удалять свой товар."""
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('catalog:product_delete', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_update_product(self):
        """Другой юзер не может редактировать чужой товар — 403."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('catalog:product_update', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_delete_product(self):
        """Другой юзер не может удалять чужой товар — 403."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('catalog:product_delete', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_moderator_can_update_any_product(self):
        """Модератор может редактировать любой товар."""
        self.client.force_login(self.moderator)
        response = self.client.get(
            reverse('catalog:product_update', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_moderator_can_delete_any_product(self):
        """Модератор может удалять любой товар."""
        self.client.force_login(self.moderator)
        response = self.client.get(
            reverse('catalog:product_delete', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_moderator_can_toggle_publish(self):
        """Модератор может снять товар с публикации."""
        self.client.force_login(self.moderator)
        response = self.client.post(
            reverse('catalog:product_toggle_publish', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 302)

        self.product.refresh_from_db()
        self.assertFalse(self.product.is_published)

    def test_owner_cannot_toggle_publish(self):
        """Владелец НЕ может менять статус публикации — только модератор."""
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('catalog:product_toggle_publish', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 403)

        self.product.refresh_from_db()
        self.assertTrue(self.product.is_published)

    def test_other_user_cannot_toggle_publish(self):
        """Другой юзер не может менять статус публикации — 403."""
        self.client.force_login(self.other)
        response = self.client.post(
            reverse('catalog:product_toggle_publish', args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 403)


class HomeViewFilterTests(TestCase):
    """Тесты фильтра главной страницы по ролям."""

    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(
            email='owner@test.ru',
            password='test12345',
        )
        self.moderator = User.objects.create_user(
            email='moder@test.ru',
            password='test12345',
        )
        perm = Permission.objects.get(
            codename='can_unpublish_product',
            content_type__app_label='catalog',
        )
        self.moderator.user_permissions.add(perm)

        self.category = Category.objects.create(name='Семена', slug='semena')

        # Опубликованный чужой товар
        self.published = Product.objects.create(
            category=self.category,
            name='Опубликованный',
            slug='published',
            description='Опубликован',
            price=100,
            is_published=True,
        )
        # Неопубликованный товар владельца
        self.draft = Product.objects.create(
            category=self.category,
            owner=self.owner,
            name='Черновик',
            slug='draft',
            description='Черновик',
            price=200,
            is_published=False,
        )

    def test_anonymous_sees_only_published(self):
        """Аноним видит только опубликованные."""
        response = self.client.get(reverse('catalog:home'))
        products = response.context['object_list']
        names = [p.name for p in products]
        self.assertIn('Опубликованный', names)
        self.assertNotIn('Черновик', names)

    def test_owner_sees_own_draft(self):
        """Владелец видит свой черновик на главной."""
        self.client.force_login(self.owner)
        response = self.client.get(reverse('catalog:home'))
        products = response.context['object_list']
        names = [p.name for p in products]
        self.assertIn('Опубликованный', names)
        self.assertIn('Черновик', names)

    def test_moderator_sees_all(self):
        """Модератор видит все товары, включая черновики."""
        self.client.force_login(self.moderator)
        response = self.client.get(reverse('catalog:home'))
        products = response.context['object_list']
        names = [p.name for p in products]
        self.assertIn('Опубликованный', names)
        self.assertIn('Черновик', names)


class ProductDraftVisibilityTests(TestCase):
    """Тесты скрытия черновиков товаров от чужих по прямой ссылке (404)."""

    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(
            email='owner@test.ru',
            password='test12345',
        )
        self.other = User.objects.create_user(
            email='other@test.ru',
            password='test12345',
        )
        self.moderator = User.objects.create_user(
            email='moder@test.ru',
            password='test12345',
        )
        perm = Permission.objects.get(
            codename='can_unpublish_product',
            content_type__app_label='catalog',
        )
        self.moderator.user_permissions.add(perm)

        self.category = Category.objects.create(name='Семена', slug='semena')

        # Черновик владельца (is_published=False)
        self.draft = Product.objects.create(
            category=self.category,
            owner=self.owner,
            name='Черновик',
            slug='draft',
            description='Скрытый',
            price=100,
            is_published=False,
        )

    def test_anonymous_cannot_view_draft(self):
        """Аноним не может открыть черновик по прямой ссылке — 404."""
        response = self.client.get(
            reverse('catalog:product_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_view_draft(self):
        """Другой юзер не может открыть чужой черновик — 404."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('catalog:product_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_own_draft(self):
        """Владелец видит свой черновик — 200."""
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('catalog:product_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_moderator_can_view_any_draft(self):
        """Модератор видит любой черновик — 200."""
        self.client.force_login(self.moderator)
        response = self.client.get(
            reverse('catalog:product_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 200)
