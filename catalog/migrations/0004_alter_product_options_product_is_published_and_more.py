# Авто-миграция Django: добавляет поля owner и is_published,
# а также регистрирует кастомное право can_unpublish_product в Meta.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0003_contact'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={
                'ordering': ['-created_at'],
                'permissions': [
                    ('can_unpublish_product', 'Может отменять публикацию продукта'),
                ],
                'verbose_name': 'Продукт',
                'verbose_name_plural': 'Продукты',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='is_published',
            field=models.BooleanField(
                default=False,
                verbose_name='Опубликован',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Владелец',
            ),
        ),
    ]
