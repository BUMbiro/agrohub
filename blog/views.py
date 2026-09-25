from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .models import BlogPost
from .forms import BlogPostForm


class BlogPostListView(ListView):
    """Список статей блога (только опубликованные)."""

    model = BlogPost
    template_name = 'blog/blogpost_list.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        """Только опубликованные статьи."""
        return BlogPost.objects.filter(is_published=True)


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
        return obj


class BlogPostCreateView(CreateView):
    """Создание статьи."""

    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/blogpost_form.html'
    success_url = reverse_lazy('blog:blogpost_list')


class BlogPostUpdateView(UpdateView):
    """Редактирование статьи. После сохранения — на страницу статьи."""

    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/blogpost_form.html'

    def get_success_url(self):
        """Редирект на страницу отредактированной статьи."""
        return reverse_lazy('blog:blogpost_detail', kwargs={'pk': self.object.pk})


class BlogPostDeleteView(DeleteView):
    """Удаление статьи."""

    model = BlogPost
    template_name = 'blog/blogpost_confirm_delete.html'
    success_url = reverse_lazy('blog:blogpost_list')
