# Generated by Django 3.2.16 on 2022-12-15 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0005_remove_translation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
    ]