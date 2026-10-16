from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


# Имя группы модераторов — используется и в других местах проекта
MODERATOR_GROUP_NAME = 'Модератор продуктов'


class Command(BaseCommand):
    """Создаёт группу «Модератор продуктов» и назначает ей права:

    - can_unpublish_product — может отменять публикацию товара (кастомное право);
    - delete_product — может удалять любой товар.
    """

    help = 'Создаёт группу «Модератор продуктов» с правами модерации'

    def handle(self, *args, **options):
        # 1. Создаём группу (или берём существующую)
        group, created = Group.objects.get_or_create(name=MODERATOR_GROUP_NAME)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Группа «{MODERATOR_GROUP_NAME}» создана.'))
        else:
            self.stdout.write(f'Группа «{MODERATOR_GROUP_NAME}» уже существует — обновляем права.')

        # 2. Находим нужные права по коду (codename)
        #    codename кастомного права задан в Meta.permissions модели Product
        try:
            can_unpublish = Permission.objects.get(
                codename='can_unpublish_product',
                content_type__app_label='catalog',
            )
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Право can_unpublish_product не найдено. '
                'Убедись, что миграции применены (право создаётся миграцией).'
            ))
            return

        try:
            delete_product = Permission.objects.get(
                codename='delete_product',
                content_type__app_label='catalog',
            )
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR('Право delete_product не найдено.'))
            return

        # 3. Назначаем оба права группе
        group.permissions.set([can_unpublish, delete_product])

        self.stdout.write(self.style.SUCCESS(
            f'Группе «{MODERATOR_GROUP_NAME}» назначены права: '
            f'can_unpublish_product, delete_product.'
        ))
