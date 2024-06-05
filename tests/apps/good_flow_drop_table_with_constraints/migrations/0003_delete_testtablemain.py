from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("good_flow_drop_table_with_constraints", "0002_remove_testtablechild_main"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TestTableMain",
        ),
    ]
