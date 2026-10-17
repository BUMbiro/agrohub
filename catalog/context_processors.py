from .models import Category


def menu_categories(request):
    """Добавляет список категорий во все шаблоны (для меню)."""
    return {
        'categories': Category.objects.all(),
    }
