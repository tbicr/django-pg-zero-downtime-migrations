from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        (
            "good_flow_drop_column_with_constraints",
            "0006_remove_testtablemain_field_i4",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="testtablemain",
            name="field_i3",
        ),
    ]
