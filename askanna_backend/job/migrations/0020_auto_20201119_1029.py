# Generated by Django 2.2.8 on 2020-11-19 10:29

from django.db import migrations
import encrypted_model_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0019_jobvariable_is_masked'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobvariable',
            name='value',
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
    ]
