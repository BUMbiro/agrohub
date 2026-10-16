from django.contrib import admin

from .models import Category, Product, News, Contact


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка категорий: id и name в списке."""

    list_display = ('id', 'name')              # колонки в списке
    search_fields = ('name',)                  # поиск по имени
    prepopulated_fields = {'slug': ('name',)}  # slug автозаполняется из name


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка продуктов.

    Показывает владельца и статус публикации, даёт фильтр по статусу
    и позволяет переключать is_published прямо из списка.
    """

    list_display = ('id', 'name', 'price', 'category', 'owner', 'is_published')
    list_filter = ('category', 'is_published')            # фильтры справа
    list_editable = ('is_published',)                     # переключение прямо в списке
    search_fields = ('name', 'description')               # поиск по имени и описанию
    list_select_related = ('category', 'owner')           # оптимизация запросов
    prepopulated_fields = {'slug': ('name',)}             # slug автозаполняется из name


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Админка новостей (по желанию — для удобства)."""

    list_display = ('id', 'title', 'date')
    search_fields = ('title', 'content')
    list_filter = ('date',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Админка контактов: id, name, phone, email."""

    list_display = ('id', 'name', 'phone', 'email')
