# Generated by Django 3.2.16 on 2022-12-15 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_user_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='use_global_profile',
            field=models.BooleanField(default=True, help_text='Use information from the global user account', verbose_name='Use AskAnna profile'),
        ),
    ]
