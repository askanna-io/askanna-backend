# Generated by Django 2.2.8 on 2020-11-25 13:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_auto_20201124_0223'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='membership',
            name='users_membe_user_id_a4ecb3_idx',
        ),
        migrations.AlterUniqueTogether(
            name='membership',
            unique_together={('user', 'object_uuid', 'object_type', 'deleted')},
        ),
    ]