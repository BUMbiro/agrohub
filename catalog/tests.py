from django.test import TestCase, Client
from django.urls import reverse

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
        """Аноним может смотреть детальную товара."""
        response = self.client.get(reverse('catalog:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
