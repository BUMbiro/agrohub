from django.contrib import admin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Админка статей блога."""

    list_display = ('id', 'title', 'is_published', 'views', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    list_editable = ('is_published',)
    readonly_fields = ('views', 'created_at', 'updated_at')
