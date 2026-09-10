from django.core.management.base import BaseCommand
from django.core.management import call_command

from catalog.models import Category, Product


class Command(BaseCommand):
    """Кастомная команда: очищает БД и загружает фикстуры Category и Product."""

    help = 'Удаляет старые данные и загружает фикстуры категорий и продуктов'

    def handle(self, *args, **options):
        # 1. Сообщаем о старте
        self.stdout.write('Очистка старых данных...')

        # 2. Удаляем продукты первыми — иначе FK не даст удалить категории
        Product.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Старые данные удалены.'))

        # 3. Загружаем фикстуры по очереди: сначала категории, потом продукты
        self.stdout.write('Загрузка фикстур...')
        call_command('loaddata', 'categories.json', verbosity=0)
        call_command('loaddata', 'products.json', verbosity=0)

        # 4. Финальный отчёт
        self.stdout.write(self.style.SUCCESS(
            f'Загружено категорий: {Category.objects.count()}, '
            f'продуктов: {Product.objects.count()}'
        ))
