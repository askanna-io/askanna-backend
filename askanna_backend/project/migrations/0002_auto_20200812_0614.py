# Generated by Django 2.2.8 on 2020-08-12 06:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'ordering': ['name']},
        ),
        migrations.RemoveField(
            model_name='project',
            name='title',
        ),
    ]