# Generated by Django 3.2.15 on 2022-09-22 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("run", "0004_move_run_result"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="result",
            options={"ordering": ["-created"]},
        ),
    ]
