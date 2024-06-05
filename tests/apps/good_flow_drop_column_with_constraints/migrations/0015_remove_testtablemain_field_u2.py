from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        (
            "good_flow_drop_column_with_constraints",
            "0014_remove_testtablemain_field_u3",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="testtablemain",
            name="field_u2",
        ),
    ]
