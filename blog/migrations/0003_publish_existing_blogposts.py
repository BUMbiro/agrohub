# Data-миграция: публикует существующие статьи блога.
# Раньше is_published был default=True, теперь default=False.
# Чтобы уже написанные статьи не стали внезапно черновиками — публикуем их.
# Автора проставляем первому суперюзеру, если он есть (чтобы у статей был владелец).

from django.db import migrations


def publish_existing(apps, schema_editor):
    """Публикуем существующие статьи и назначаем им автора (первый суперюзер)."""
    BlogPost = apps.get_model('blog', 'BlogPost')
    User = apps.get_model('users', 'User')

    # Находим первого суперюзера (обычно admin@agrohub.local)
    admin = User.objects.filter(is_superuser=True).first()

    # Публикуем все существующие статьи
    BlogPost.objects.all().update(is_published=True)

    # Назначаем автора, если он есть и у статьи автор ещё не проставлен
    if admin:
        BlogPost.objects.filter(author__isnull=True).update(author=admin)


def unpublish_all(apps, schema_editor):
    """Откат: снимаем с публикации и обнуляем автора."""
    BlogPost = apps.get_model('blog', 'BlogPost')
    BlogPost.objects.all().update(is_published=False, author=None)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_alter_blogpost_options_blogpost_author_and_more'),
        ('users', '0001_initial'),   # нужна, чтобы apps.get_model('users', 'User') работал
    ]

    operations = [
        migrations.RunPython(publish_existing, unpublish_all),
    ]
