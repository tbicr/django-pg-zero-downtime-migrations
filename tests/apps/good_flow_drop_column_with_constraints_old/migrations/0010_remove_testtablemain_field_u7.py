from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        (
            "good_flow_drop_column_with_constraints_old",
            "0009_remove_testtablemain_field_i1",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="testtablemain",
            name="field_u7",
        ),
    ]
