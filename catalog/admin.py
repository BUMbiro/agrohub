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
    """Админка продуктов: id, name, price, category + фильтр и поиск."""

    list_display = ('id', 'name', 'price', 'category')   # колонки
    list_filter = ('category',)                          # фильтр справа по категории
    search_fields = ('name', 'description')              # поиск по имени и описанию
    list_select_related = ('category',)                  # оптимизация: подтягиваем категорию одним запросом
    prepopulated_fields = {'slug': ('name',)}            # slug автозаполняется из name


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
