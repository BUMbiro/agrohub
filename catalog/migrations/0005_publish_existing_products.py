# Data-миграция: публикует все товары, которые уже были в БД
# до появления поля is_published. Нужно, чтобы после добавления
# поля (default=False) каталог не оказался пустым.

from django.db import migrations


def publish_existing(apps, schema_editor):
    """Публикуем все существующие товары."""
    Product = apps.get_model('catalog', 'Product')
    Product.objects.all().update(is_published=True)


def unpublish_all(apps, schema_editor):
    """Откат: помечаем все товары как неопубликованные."""
    Product = apps.get_model('catalog', 'Product')
    Product.objects.all().update(is_published=False)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_alter_product_options_product_is_published_and_more'),
    ]

    operations = [
        migrations.RunPython(publish_existing, unpublish_all),
    ]
