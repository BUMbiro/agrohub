from django.contrib import admin

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Админка статей блога.

    Показывает автора и статус публикации, даёт фильтр по статусу и автору,
    позволяет переключать is_published прямо из списка.
    """

    list_display = ('id', 'title', 'author', 'is_published', 'views', 'created_at')
    list_filter = ('is_published', 'created_at', 'author')
    search_fields = ('title', 'content', 'author__email')
    list_editable = ('is_published',)
    list_select_related = ('author',)                      # оптимизация: подтягиваем автора одним запросом
    readonly_fields = ('views', 'created_at', 'updated_at')
    autocomplete_fields = ('author',)                       # удобный поиск автора в форме
