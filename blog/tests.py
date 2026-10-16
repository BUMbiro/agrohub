from django.test import TestCase, Client
from django.urls import reverse

from .models import BlogPost


class BlogPostPermissionsTests(TestCase):
    """Тесты защиты CRUD статей блога от анонимов."""

    def setUp(self):
        self.client = Client()
        self.post = BlogPost.objects.create(
            title='Как выбрать семена',
            content='Текст статьи',
            is_published=True,
        )

    def test_anonymous_cannot_create_post(self):
        """Аноним не может открыть форму создания."""
        response = self.client.get(reverse('blog:blogpost_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_anonymous_cannot_update_post(self):
        """Аноним не может редактировать статью."""
        response = self.client.get(reverse('blog:blogpost_update', args=[self.post.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_anonymous_cannot_delete_post(self):
        """Аноним не может удалять статью."""
        response = self.client.get(reverse('blog:blogpost_delete', args=[self.post.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_anonymous_can_view_post_list(self):
        """Аноним может смотреть список статей."""
        response = self.client.get(reverse('blog:blogpost_list'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_view_post_detail(self):
        """Аноним может смотреть детальную статьи."""
        response = self.client.get(reverse('blog:blogpost_detail', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)


class BlogPostViewsCounterTests(TestCase):
    """Тест счётчика просмотров."""

    def setUp(self):
        self.client = Client()
        self.post = BlogPost.objects.create(
            title='Тест просмотров',
            content='Текст',
            is_published=True,
        )

    def test_views_increment_on_detail(self):
        """При открытии статьи счётчик растёт."""
        initial_views = self.post.views
        self.client.get(reverse('blog:blogpost_detail', args=[self.post.pk]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, initial_views + 1)
