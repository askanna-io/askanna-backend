# Generated by Django 4.1.7 on 2023-03-30 12:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("job", "0018_change_meta_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobdef",
            name="environment_image",
            field=models.CharField(blank=True, default="", editable=False, max_length=2048),
            preserve_default=False,
        ),
    ]
