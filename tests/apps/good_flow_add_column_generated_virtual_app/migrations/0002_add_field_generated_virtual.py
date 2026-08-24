from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("good_flow_add_column_generated_virtual_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="testtable",
            name="field_generated",
            field=models.GeneratedField(
                expression=models.F("field_int") + models.F("field_int"),
                output_field=models.IntegerField(),
                db_persist=False,
            ),
        ),
    ]
