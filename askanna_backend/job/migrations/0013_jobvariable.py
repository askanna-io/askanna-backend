# Generated by Django 2.2.8 on 2020-05-28 10:12

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import encrypted_model_fields.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
        ('job', '0012_remove_jobartifact_jobdef'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobVariable',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32)),
                ('name', models.CharField(max_length=128)),
                ('value', encrypted_model_fields.fields.EncryptedTextField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variable', to='project.Project')),
            ],
            options={
                'verbose_name': 'Job Variable',
                'verbose_name_plural': 'Job Variables',
                'ordering': ['-created'],
            },
        ),
    ]