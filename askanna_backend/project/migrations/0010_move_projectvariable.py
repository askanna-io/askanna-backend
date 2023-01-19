from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0009_description_do_not_allow_null_default_empty_string"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="ProjectVariable",
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="ProjectVariable",
                    table="variable_variable",
                ),
            ],
        ),
    ]
