# Generated by Django 2.2.8 on 2020-09-02 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20200519_2129'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='role',
            field=models.CharField(choices=[('WM', 'Member'), ('WA', 'Admin')], default='WM', max_length=2),
        ),
    ]