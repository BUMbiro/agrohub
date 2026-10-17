from django.core.cache import cache

from catalog.models import Product, Category


# TTL кэша — 5 минут (300 секунд)
CATEGORY_CACHE_TTL = 300


def _serialize_product(product):
    """Преобразует Product в словарь для кэша.

    Кэш (Redis) не умеет хранить QuerySet или объекты моделей —
    только примитивы. Поэтому сериализуем нужные поля в dict.
    """
    return {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'price': str(product.price),       # Decimal → str (JSON-совместимо)
        'unit': product.unit,
        'image_url': product.image.url if product.image else None,
        'in_stock': product.in_stock,
        'is_published': product.is_published,
        'category_id': product.category_id,
        'category_name': product.category.name,
        'category_slug': product.category.slug,
    }


def get_products_by_category(category_id):
    """Возвращает список продуктов в указанной категории.

    Логика:
    1. Пытаемся взять из Redis по ключу `category_{id}`.
    2. Если в кэше нет — идём в БД, сериализуем, кладём в кэш с TTL=300.
    3. Возвращаем список словарей (не QuerySet).

    Кэшируются только опубликованные продукты (is_published=True).
    Черновики и скрытые товары в кэш не попадают — это важно для безопасности.
    """
    cache_key = f'category_{category_id}'

    # 1. Пытаемся взять из кэша
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # 2. Кэш пуст — идём в БД
    products = (
        Product.objects
        .filter(category_id=category_id, is_published=True)
        .select_related('category')
        .order_by('-created_at')
    )

    # 3. Сериализуем в список словарей
    data = [_serialize_product(p) for p in products]

    # 4. Кладём в кэш с TTL
    cache.set(cache_key, data, timeout=CATEGORY_CACHE_TTL)

    return data
