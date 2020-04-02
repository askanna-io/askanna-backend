# Generated by Django 2.2.8 on 2020-04-02 12:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0003_auto_20200402_0801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobrun',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='jobrun',
            name='payload',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='job.JobPayload'),
        ),
    ]
