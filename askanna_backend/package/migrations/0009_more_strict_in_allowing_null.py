# Generated by Django 4.1.7 on 2023-03-30 12:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0008_move_field_to_core_iso_third_party_app"),
    ]

    operations = [
        migrations.AlterField(
            model_name="package",
            name="name",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
    ]
