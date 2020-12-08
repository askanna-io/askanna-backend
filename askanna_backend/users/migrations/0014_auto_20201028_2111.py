# Generated by Django 2.2.8 on 2020-10-28 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_invitation_front_end_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='short_uuid',
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='short_uuid',
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
    ]