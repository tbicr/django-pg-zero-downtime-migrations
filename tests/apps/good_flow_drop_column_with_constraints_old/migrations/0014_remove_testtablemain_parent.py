from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        (
            "good_flow_drop_column_with_constraints_old",
            "0013_remove_testtablemain_main_id",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="testtablemain",
            name="parent",
        ),
    ]
