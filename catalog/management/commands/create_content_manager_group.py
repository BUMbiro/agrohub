from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


# Имя группы контент-менеджеров — используется и в других местах проекта
CONTENT_MANAGER_GROUP_NAME = 'Контент-менеджер'


class Command(BaseCommand):
    """Создаёт группу «Контент-менеджер» и назначает ей права:

    - can_unpublish_blogpost — может снимать статьи с публикации (кастомное право);
    - change_blogpost — может редактировать любые статьи;
    - delete_blogpost — может удалять любые статьи;
    - add_blogpost — может создавать статьи.
    """

    help = 'Создаёт группу «Контент-менеджер» с правами управления блогом'

    def handle(self, *args, **options):
        # 1. Создаём группу (или берём существующую)
        group, created = Group.objects.get_or_create(name=CONTENT_MANAGER_GROUP_NAME)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Группа «{CONTENT_MANAGER_GROUP_NAME}» создана.'))
        else:
            self.stdout.write(f'Группа «{CONTENT_MANAGER_GROUP_NAME}» уже существует — обновляем права.')

        # 2. Находим права по codename
        #    can_unpublish_blogpost — кастомное, задано в Meta.permissions модели BlogPost
        #    change/delete/add_blogpost — стандартные Django-права
        codenames = [
            'can_unpublish_blogpost',
            'change_blogpost',
            'delete_blogpost',
            'add_blogpost',
        ]

        permissions = []
        for codename in codenames:
            try:
                perm = Permission.objects.get(
                    codename=codename,
                    content_type__app_label='blog',
                )
                permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Право {codename} не найдено. '
                    f'Убедись, что миграции применены.'
                ))
                return

        # 3. Назначаем права группе
        group.permissions.set(permissions)

        self.stdout.write(self.style.SUCCESS(
            f'Группе «{CONTENT_MANAGER_GROUP_NAME}» назначены права: '
            f'{", ".join(codenames)}.'
        ))
