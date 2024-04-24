from django.db import migrations, models


def insert_objects(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    TestTable = apps.get_model("idempotency_create_table_app", "TestTable")
    TestTable.objects.using(db_alias).create(test_field_int=1)


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TestTable",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("test_field_int", models.IntegerField()),
                ("test_field_str", models.CharField(max_length=10)),
            ],
        ),
        migrations.RunPython(insert_objects, migrations.RunPython.noop),
    ]
