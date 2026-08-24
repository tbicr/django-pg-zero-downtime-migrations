from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TestTable",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("test_field_int", models.IntegerField()),
                ("test_field_indexed", models.IntegerField(db_index=True)),
                ("test_field_unique", models.IntegerField(null=True, unique=True)),
            ],
            options={"db_table": "rename_and_drop_test_table_old"},
        ),
    ]
