# Generated by Django 3.2.15 on 2022-09-27 19:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0003_move_projectvariable'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projectvariable',
            options={'ordering': ['-created']},
        ),
    ]