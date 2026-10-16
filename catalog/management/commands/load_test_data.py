from django.core.management.base import BaseCommand
from django.core.management import call_command

from catalog.models import Category, Product


class Command(BaseCommand):
    """Кастомная команда: очищает БД и загружает фикстуры Category и Product.

    Дополнительно создаёт/обновляет группу «Модератор продуктов»,
    чтобы после загрузки данных можно было сразу тестировать права.
    """

    help = 'Удаляет старые данные, грузит фикстуры и создаёт группу модераторов'

    def handle(self, *args, **options):
        # 1. Очистка данных
        self.stdout.write('Очистка старых данных...')

        # Продукты удаляем первыми — иначе FK не даст удалить категории
        Product.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Старые данные удалены.'))

        # 2. Загрузка фикстур (сначала категории, потом товары)
        self.stdout.write('Загрузка фикстур...')
        call_command('loaddata', 'categories.json', verbosity=0)
        call_command('loaddata', 'products.json', verbosity=0)

        # 3. Создание/обновление группы модераторов
        self.stdout.write('Создание группы модераторов...')
        call_command('create_moderator_group')

        # 4. Финальный отчёт
        self.stdout.write(self.style.SUCCESS(
            f'Загружено категорий: {Category.objects.count()}, '
            f'продуктов: {Product.objects.count()}'
        ))
