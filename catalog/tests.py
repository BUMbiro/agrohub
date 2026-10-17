from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from users.models import User

from .models import Category, Product
from .services.products import get_products_by_category


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
            is_published=True,
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
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name='Морковь')
        self.assertEqual(product.owner, self.user)
        self.assertFalse(product.is_published)


class ProductModerationTests(TestCase):
    """Тесты прав владельца и модератора на управление товаром."""

    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(email='owner@test.ru', password='test12345')
        self.other = User.objects.create_user(email='other@test.ru', password='test12345')
        self.moderator = User.objects.create_user(email='moder@test.ru', password='test12345')

        group = Group.objects.create(name='Модератор продуктов (тест)')
        perm = Permission.objects.get(codename='can_unpublish_product', content_type__app_label='catalog')
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
        self.client.force_login(self.owner)
        response = self.client.get(reverse('catalog:product_update', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_delete_product(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('catalog:product_delete', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_update_product(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('catalog:product_update', args=[self.product.pk]))
        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_delete_product(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('catalog:product_delete', args=[self.product.pk]))
        self.assertEqual(response.status_code, 403)

    def test_moderator_can_update_any_product(self):
        self.client.force_login(self.moderator)
        response = self.client.get(reverse('catalog:product_update', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

    def test_moderator_can_delete_any_product(self):
        self.client.force_login(self.moderator)
        response = self.client.get(reverse('catalog:product_delete', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

    def test_moderator_can_toggle_publish(self):
        self.client.force_login(self.moderator)
        response = self.client.post(reverse('catalog:product_toggle_publish', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_published)

    def test_owner_cannot_toggle_publish(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('catalog:product_toggle_publish', args=[self.product.pk]))
        self.assertEqual(response.status_code, 403)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_published)

    def test_other_user_cannot_toggle_publish(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse('catalog:product_toggle_publish', args=[self.product.pk]))
        self.assertEqual(response.status_code, 403)


class HomeViewFilterTests(TestCase):
    """Тесты фильтра главной страницы по ролям."""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(email='owner@test.ru', password='test12345')
        self.moderator = User.objects.create_user(email='moder@test.ru', password='test12345')
        perm = Permission.objects.get(codename='can_unpublish_product', content_type__app_label='catalog')
        self.moderator.user_permissions.add(perm)

        self.category = Category.objects.create(name='Семена', slug='semena')
        self.published = Product.objects.create(category=self.category, name='Опубликованный', slug='published',
                                                description='Опубликован', price=100, is_published=True)
        self.draft = Product.objects.create(category=self.category, owner=self.owner, name='Черновик', slug='draft',
                                            description='Черновик', price=200, is_published=False)

    def test_anonymous_sees_only_published(self):
        response = self.client.get(reverse('catalog:home'))
        names = [p.name for p in response.context['object_list']]
        self.assertIn('Опубликованный', names)
        self.assertNotIn('Черновик', names)

    def test_owner_sees_own_draft(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('catalog:home'))
        names = [p.name for p in response.context['object_list']]
        self.assertIn('Опубликованный', names)
        self.assertIn('Черновик', names)

    def test_moderator_sees_all(self):
        self.client.force_login(self.moderator)
        response = self.client.get(reverse('catalog:home'))
        names = [p.name for p in response.context['object_list']]
        self.assertIn('Опубликованный', names)
        self.assertIn('Черновик', names)


class ProductDraftVisibilityTests(TestCase):
    """Тесты скрытия черновиков товаров от чужих по прямой ссылке (404)."""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(email='owner@test.ru', password='test12345')
        self.other = User.objects.create_user(email='other@test.ru', password='test12345')
        self.moderator = User.objects.create_user(email='moder@test.ru', password='test12345')
        perm = Permission.objects.get(codename='can_unpublish_product', content_type__app_label='catalog')
        self.moderator.user_permissions.add(perm)

        self.category = Category.objects.create(name='Семена', slug='semena')
        self.draft = Product.objects.create(category=self.category, owner=self.owner, name='Черновик', slug='draft',
                                            description='Скрытый', price=100, is_published=False)

    def test_anonymous_cannot_view_draft(self):
        response = self.client.get(reverse('catalog:product_detail', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_view_draft(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('catalog:product_detail', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_own_draft(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('catalog:product_detail', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 200)

    def test_moderator_can_view_any_draft(self):
        self.client.force_login(self.moderator)
        response = self.client.get(reverse('catalog:product_detail', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 200)


# ============================================================
# НОВЫЕ ТЕСТЫ НА КЭШИРОВАНИЕ (REDIS)
# ============================================================

class CategoryCacheTests(TestCase):
    """Тесты кэширования списка продуктов в категории."""

    def setUp(self):
        self.category = Category.objects.create(name='Кэш-категория', slug='cache-cat')
        self.product = Product.objects.create(
            category=self.category, name='Кэш-товар', slug='cache-prod',
            description='Тест', price=100, is_published=True
        )
        # Чистим кэш перед каждым тестом
        cache.delete(f'category_{self.category.id}')

    def tearDown(self):
        # Чистим кэш после теста
        cache.delete(f'category_{self.category.id}')

    def test_category_products_cached(self):
        """Сервис кладёт данные в Redis с TTL."""
        key = f'category_{self.category.id}'
        self.assertIsNone(cache.get(key))

        data = get_products_by_category(self.category.id)
        self.assertEqual(len(data), 1)

        # Проверяем, что в кэше
        cached = cache.get(key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached[0]['name'], 'Кэш-товар')

        # Проверяем TTL (он должен быть близок к 300)
        ttl = cache.ttl(key)
        self.assertIsNotNone(ttl)
        self.assertLessEqual(ttl, 300)
        self.assertGreater(ttl, 0)

    def test_category_products_from_cache(self):
        """Повторный вызов берёт данные из кэша (без запроса в БД)."""
        # Первый вызов — кэширует
        get_products_by_category(self.category.id)

        # Второй вызов не должен дергать БД
        with self.assertNumQueries(0):
            data = get_products_by_category(self.category.id)
            self.assertEqual(len(data), 1)


class ProductDetailCacheTests(TestCase):
    """Тесты кэширования детальной страницы товара."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Семена', slug='semena')

        # Опубликованный товар
        self.product = Product.objects.create(
            category=self.category, name='Опубликованный', slug='published-prod',
            description='Тест', price=100, is_published=True
        )
        # Черновик
        self.draft = Product.objects.create(
            category=self.category, name='Черновик', slug='draft-prod',
            description='Скрыт', price=200, is_published=False
        )
        # Чистим кэш
        cache.delete(f'product_detail_{self.product.id}')
        cache.delete(f'product_detail_{self.draft.id}')

    def tearDown(self):
        cache.delete(f'product_detail_{self.product.id}')
        cache.delete(f'product_detail_{self.draft.id}')

    def test_anonymous_caches_published_product(self):
        """Аноним открывает опубликованный товар — он кэшируется."""
        key = f'product_detail_{self.product.id}'
        self.assertIsNone(cache.get(key))

        response = self.client.get(reverse('catalog:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

        cached = cache.get(key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.id, self.product.id)

    def test_authenticated_does_not_cache(self):
        """Авторизованный юзер — товар НЕ кэшируется (персонализация)."""
        user = User.objects.create_user(email='cache@test.ru', password='test12345')
        self.client.force_login(user)

        key = f'product_detail_{self.product.id}'
        self.assertIsNone(cache.get(key))

        response = self.client.get(reverse('catalog:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

        # Кэш должен остаться пустым
        self.assertIsNone(cache.get(key))

    def test_anonymous_does_not_cache_draft(self):
        """Аноним не видит черновик (404) — он не кэшируется."""
        key = f'product_detail_{self.draft.id}'
        self.assertIsNone(cache.get(key))

        response = self.client.get(reverse('catalog:product_detail', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)

        self.assertIsNone(cache.get(key))
