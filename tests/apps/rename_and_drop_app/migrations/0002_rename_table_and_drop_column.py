from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("rename_and_drop_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="testtable",
            table="rename_and_drop_test_table_new",
        ),
        migrations.RemoveField(
            model_name="testtable",
            name="test_field_indexed",
        ),
        migrations.RemoveField(
            model_name="testtable",
            name="test_field_unique",
        ),
    ]
