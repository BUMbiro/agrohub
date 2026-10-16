from django.conf import settings
from django.db import models


class BlogPost(models.Model):
    """Статья блога AgroHub.

    Привязана к автору (author). Публикация управляется вручную
    контент-менеджером через право can_unpublish_blogpost.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,    # если юзера удалили — статья остаётся, author=None
        null=True,                    # null=True, чтобы миграция не падала на существующих статьях
        blank=True,
        related_name='blogposts',     # user.blogposts.all() — статьи пользователя
        verbose_name='Автор',
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок',
    )
    content = models.TextField(
        verbose_name='Содержимое',
    )
    preview = models.ImageField(
        upload_to='blog/previews/',
        blank=True,
        null=True,
        verbose_name='Превью',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата последнего изменения',
    )
    is_published = models.BooleanField(
        default=False,                # по критерию: автор пишет черновик, публикует контент-менеджер
        verbose_name='Опубликовано',
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество просмотров',
    )

    class Meta:
        verbose_name = 'Статья блога'
        verbose_name_plural = 'Статьи блога'
        ordering = ['-created_at']    # новые сверху
        permissions = [
            # Кастомное право для контент-менеджеров
            ('can_unpublish_blogpost', 'Может отменять публикацию статьи'),
        ]

    def __str__(self):
        return self.title

    # --------------------------------------------------------
    # Хелперы прав доступа
    # --------------------------------------------------------

    def can_be_managed_by(self, user):
        """Может ли пользователь редактировать/удалять эту статью.

        Доступ разрешён:
        - автору статьи;
        - контент-менеджеру (право can_unpublish_blogpost);
        - суперпользователю.

        Модератор продуктов (can_unpublish_product) сюда НЕ входит —
        это другой отдел.
        """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if self.author_id == user.id:                          # автор статьи
            return True
        return user.has_perm('blog.can_unpublish_blogpost')    # контент-менеджер

    def can_be_unpublished_by(self, user):
        """Может ли пользователь менять статус публикации статьи.

        Только контент-менеджер или суперюзер. Автор сам публиковать
        не может — только пишет черновик.
        """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.has_perm('blog.can_unpublish_blogpost')
