# Generated by Django 2.2.8 on 2020-03-31 06:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '__first__'),
        ('package', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='package',
            name='project_id',
        ),
        migrations.AddField(
            model_name='package',
            name='project',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='packages', related_query_name='package', to='project.Project'),
        ),
    ]