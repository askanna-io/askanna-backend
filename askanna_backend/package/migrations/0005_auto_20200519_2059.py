# Generated by Django 2.2.8 on 2020-05-19 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0004_auto_20200519_1350'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='package',
            options={'ordering': ['-created']},
        ),
        migrations.RemoveField(
            model_name='package',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='package',
            name='deleted_at',
        ),
    ]