# Generated by Django 2.2.8 on 2020-10-13 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20201005_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='Name of User'),
        ),
    ]
