from django.contrib.auth.models import Group, Permission
from django.test import TestCase, Client
from django.urls import reverse

from users.models import User

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
        """Аноним может смотреть детальную опубликованной статьи."""
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


class BlogPostAuthorTests(TestCase):
    """Тесты привязки статьи к автору."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@test.ru',
            password='test12345',
        )
        self.client.force_login(self.user)

    def test_author_is_set_on_create(self):
        """При создании статьи author = текущий юзер, is_published=False."""
        response = self.client.post(
            reverse('blog:blogpost_create'),
            data={
                'title': 'Моя статья',
                'content': 'Текст моей статьи',
            },
        )
        self.assertEqual(response.status_code, 302)

        post = BlogPost.objects.get(title='Моя статья')
        self.assertEqual(post.author, self.user)
        self.assertFalse(post.is_published)


class BlogPostManagementTests(TestCase):
    """Тесты прав автора и контент-менеджера."""

    def setUp(self):
        self.client = Client()

        self.author = User.objects.create_user(
            email='author@test.ru',
            password='test12345',
        )
        self.other = User.objects.create_user(
            email='other@test.ru',
            password='test12345',
        )
        self.content_manager = User.objects.create_user(
            email='cm@test.ru',
            password='test12345',
        )
        group = Group.objects.create(name='Контент-менеджер (тест)')
        perm = Permission.objects.get(
            codename='can_unpublish_blogpost',
            content_type__app_label='blog',
        )
        group.permissions.add(perm)
        self.content_manager.groups.add(group)

        self.post = BlogPost.objects.create(
            author=self.author,
            title='Статья автора',
            content='Текст',
            is_published=True,
        )

    def test_author_can_update_own_post(self):
        """Автор может редактировать свою статью."""
        self.client.force_login(self.author)
        response = self.client.get(
            reverse('blog:blogpost_update', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_author_can_delete_own_post(self):
        """Автор может удалять свою статью."""
        self.client.force_login(self.author)
        response = self.client.get(
            reverse('blog:blogpost_delete', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_update_post(self):
        """Другой юзер не может редактировать чужую статью — 403."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('blog:blogpost_update', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_delete_post(self):
        """Другой юзер не может удалять чужую статью — 403."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('blog:blogpost_delete', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_content_manager_can_update_any_post(self):
        """Контент-менеджер может редактировать любую статью."""
        self.client.force_login(self.content_manager)
        response = self.client.get(
            reverse('blog:blogpost_update', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_content_manager_can_delete_any_post(self):
        """Контент-менеджер может удалять любую статью."""
        self.client.force_login(self.content_manager)
        response = self.client.get(
            reverse('blog:blogpost_delete', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_content_manager_can_toggle_publish(self):
        """Контент-менеджер может снять статью с публикации."""
        self.client.force_login(self.content_manager)
        response = self.client.post(
            reverse('blog:blogpost_toggle_publish', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 302)

        self.post.refresh_from_db()
        self.assertFalse(self.post.is_published)

    def test_author_cannot_toggle_publish(self):
        """Автор НЕ может менять статус публикации — только контент-менеджер."""
        self.client.force_login(self.author)
        response = self.client.post(
            reverse('blog:blogpost_toggle_publish', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 403)

        self.post.refresh_from_db()
        self.assertTrue(self.post.is_published)

    def test_other_user_cannot_toggle_publish(self):
        """Другой юзер не может менять статус публикации — 403."""
        self.client.force_login(self.other)
        response = self.client.post(
            reverse('blog:blogpost_toggle_publish', args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 403)


class BlogPostListViewFilterTests(TestCase):
    """Тесты фильтра списка блога по ролям."""

    def setUp(self):
        self.client = Client()

        self.author = User.objects.create_user(
            email='author@test.ru',
            password='test12345',
        )
        self.content_manager = User.objects.create_user(
            email='cm@test.ru',
            password='test12345',
        )
        # Через группу — как в реальном проекте (и кэш прав сбрасывается корректно)
        group = Group.objects.create(name='Контент-менеджер (тест-фильтр)')
        perm = Permission.objects.get(
            codename='can_unpublish_blogpost',
            content_type__app_label='blog',
        )
        group.permissions.add(perm)
        self.content_manager.groups.add(group)

        # Опубликованная чужая статья
        self.published = BlogPost.objects.create(
            title='Опубликованная',
            content='Текст',
            is_published=True,
        )
        # Черновик автора
        self.draft = BlogPost.objects.create(
            author=self.author,
            title='Черновик',
            content='Текст',
            is_published=False,
        )

    def test_anonymous_sees_only_published(self):
        """Аноним видит только опубликованные."""
        response = self.client.get(reverse('blog:blogpost_list'))
        posts = response.context['posts']
        titles = [p.title for p in posts]
        self.assertIn('Опубликованная', titles)
        self.assertNotIn('Черновик', titles)

    def test_author_sees_own_draft(self):
        """Автор видит свой черновик в списке."""
        self.client.force_login(self.author)
        response = self.client.get(reverse('blog:blogpost_list'))
        posts = response.context['posts']
        titles = [p.title for p in posts]
        self.assertIn('Опубликованная', titles)
        self.assertIn('Черновик', titles)

    def test_content_manager_sees_all(self):
        """Контент-менеджер видит все статьи, включая черновики."""
        self.client.force_login(self.content_manager)
        response = self.client.get(reverse('blog:blogpost_list'))
        posts = response.context['posts']
        titles = [p.title for p in posts]
        self.assertIn('Опубликованная', titles)
        self.assertIn('Черновик', titles)


class BlogPostDraftVisibilityTests(TestCase):
    """Тесты скрытия черновиков статей от чужих по прямой ссылке (404)."""

    def setUp(self):
        self.client = Client()

        self.author = User.objects.create_user(
            email='author@test.ru',
            password='test12345',
        )
        self.other = User.objects.create_user(
            email='other@test.ru',
            password='test12345',
        )
        self.content_manager = User.objects.create_user(
            email='cm@test.ru',
            password='test12345',
        )
        # Через группу — надёжнее, чем user_permissions.add
        group = Group.objects.create(name='Контент-менеджер (тест-черновик)')
        perm = Permission.objects.get(
            codename='can_unpublish_blogpost',
            content_type__app_label='blog',
        )
        group.permissions.add(perm)
        self.content_manager.groups.add(group)

        # Черновик автора
        self.draft = BlogPost.objects.create(
            author=self.author,
            title='Черновик',
            content='Текст',
            is_published=False,
        )

    def test_anonymous_cannot_view_draft(self):
        """Аноним не может открыть черновик по прямой ссылке — 404."""
        response = self.client.get(
            reverse('blog:blogpost_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_view_draft(self):
        """Другой юзер не может открыть чужой черновик — 404."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('blog:blogpost_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_author_can_view_own_draft(self):
        """Автор видит свой черновик — 200."""
        self.client.force_login(self.author)
        response = self.client.get(
            reverse('blog:blogpost_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_content_manager_can_view_any_draft(self):
        """Контент-менеджер видит любой черновик — 200."""
        self.client.force_login(self.content_manager)
        response = self.client.get(
            reverse('blog:blogpost_detail', args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_views_not_incremented_on_404(self):
        """Счётчик просмотров не растёт, если черновик не доступен."""
        initial_views = self.draft.views
        self.client.get(
            reverse('blog:blogpost_detail', args=[self.draft.pk])
        )
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.views, initial_views)
