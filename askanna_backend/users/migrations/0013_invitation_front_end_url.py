# Generated by Django 2.2.8 on 2020-10-26 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_auto_20201013_0653'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='front_end_url',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
