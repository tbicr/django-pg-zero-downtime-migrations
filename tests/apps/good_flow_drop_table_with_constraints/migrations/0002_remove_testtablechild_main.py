from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("good_flow_drop_table_with_constraints", "0001_initial"),
    ]

    operations = [
        # emulate worst case untracked constraints
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name="testtablechild",
                    name="main",
                ),
            ],
        ),
    ]
