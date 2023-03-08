# Generated by Django 3.2.16 on 2022-11-07 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0006_uuid_and_suuid_field_config'),
        ('package', '0003_uuid_and_suuid_field_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='project',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='packages', to='project.project'),
        ),
    ]