from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, View
)

from .models import BlogPost
from .forms import BlogPostForm


# ============================================================
# Миксин для проверки прав на управление статьёй
# ============================================================

class BlogPostPermissionMixin:
    """Миксин для вьюх редактирования/удаления статьи.

    Проверяет, что пользователь может управлять объектом:
    - автор статьи;
    - контент-менеджер (право can_unpublish_blogpost);
    - суперюзер.

    Если прав нет — отдаём 403.
    """

    def dispatch(self, request, *args, **kwargs):
        # Сначала проверяем, что пользователь авторизован
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Достаём статью (нужна для проверки прав)
        self.object = self.get_object()

        # Проверяем право управления через хелпер на модели
        if not self.object.can_be_managed_by(request.user):
            raise PermissionDenied('У вас нет прав на управление этой статьёй.')

        return super().dispatch(request, *args, **kwargs)


# ============================================================
# Список статей
# ============================================================

class BlogPostListView(ListView):
    """Список статей блога.

    Логика отображения:
    - аноним и обычный юзер — только опубликованные;
    - контент-менеджер — все (включая черновики);
    - автор — свои (включая черновики) + опубликованные чужие.
    """

    model = BlogPost
    template_name = 'blog/blogpost_list.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        """Фильтруем статьи по роли пользователя."""
        qs = BlogPost.objects.select_related('author')

        user = self.request.user

        # Аноним — только опубликованные
        if not user.is_authenticated:
            return qs.filter(is_published=True)

        # Контент-менеджер или суперюзер — видят всё
        if user.is_superuser or user.has_perm('blog.can_unpublish_blogpost'):
            return qs

        # Автор — свои (любые) + опубликованные чужие
        return qs.filter(Q(is_published=True) | Q(author=user))


# ============================================================
# Детальная статья
# ============================================================

class BlogPostDetailView(DetailView):
    """Детальная страница статьи. Увеличивает счётчик просмотров."""

    model = BlogPost
    template_name = 'blog/blogpost_detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        """При открытии статьи увеличиваем счётчик просмотров."""
        obj = super().get_object(queryset)
        obj.views += 1
        obj.save(update_fields=['views'])

        # При достижении 100 просмотров — поздравительное письмо
        if obj.views == 100:
            send_mail(
                subject='🎉 Ваша статья достигла 100 просмотров!',
                message=(
                    f'Поздравляем!\n\n'
                    f'Статья «{obj.title}» набрала 100 просмотров.\n'
                    f'Продолжайте в том же духе!\n\n'
                    f'— AgroHub'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
            print('📧 Поздравительное письмо отправлено (см. консоль выше)')

        return obj


# ============================================================
# CRUD статей
# ============================================================

class BlogPostCreateView(LoginRequiredMixin, CreateView):
    """Создание статьи. Только для авторизованных.

    Автоматически привязывает статью к текущему пользователю (author).
    Статья создаётся как черновик (is_published=False) — публикует контент-менеджер.
    """

    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/blogpost_form.html'
    success_url = reverse_lazy('blog:blogpost_list')

    def form_valid(self, form):
        """Проставляем автора перед сохранением."""
        post = form.save(commit=False)
        post.author = self.request.user     # по критерию: автор заполняется автоматом
        post.save()
        self.object = post
        return redirect(self.get_success_url())


class BlogPostUpdateView(LoginRequiredMixin, BlogPostPermissionMixin, UpdateView):
    """Редактирование статьи.

    Доступно только автору, контент-менеджеру или суперюзеру.
    """

    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/blogpost_form.html'

    def get_success_url(self):
        """Редирект на страницу отредактированной статьи."""
        return reverse_lazy('blog:blogpost_detail', kwargs={'pk': self.object.pk})


class BlogPostDeleteView(LoginRequiredMixin, BlogPostPermissionMixin, DeleteView):
    """Удаление статьи с подтверждением.

    Доступно только автору, контент-менеджеру или суперюзеру.
    """

    model = BlogPost
    template_name = 'blog/blogpost_confirm_delete.html'
    context_object_name = 'post'
    success_url = reverse_lazy('blog:blogpost_list')


class BlogPostTogglePublishView(LoginRequiredMixin, View):
    """Переключение статуса публикации статьи.

    Доступно только контент-менеджеру или суперюзеру.
    Если статья опубликована — снимаем, иначе — публикуем.
    """

    def post(self, request, pk):
        post = get_object_or_404(BlogPost, pk=pk)

        # Проверяем право на изменение публикации
        if not post.can_be_unpublished_by(request.user):
            raise PermissionDenied('У вас нет прав на изменение публикации.')

        # Переключаем статус
        post.is_published = not post.is_published
        post.save(update_fields=['is_published', 'updated_at'])

        # Сообщение пользователю
        if post.is_published:
            messages.success(request, f'Статья «{post.title}» опубликована.')
        else:
            messages.warning(request, f'Статья «{post.title}» снята с публикации.')

        # Редирект обратно на страницу статьи
        return redirect('blog:blogpost_detail', pk=post.pk)
