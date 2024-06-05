import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TestTableMain",
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
                ("main_id", models.IntegerField(null=True, unique=True)),
            ],
            options={
                "db_table": "drop_tbl_test_table_main",
            },
        ),
        migrations.CreateModel(
            name="TestTableParent",
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
            ],
            options={
                "db_table": "drop_tbl_test_table_parent",
            },
        ),
        migrations.CreateModel(
            name="TestTableChild",
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
                (
                    "main",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="good_flow_drop_table_with_constraints.testtablemain",
                        to_field="main_id",
                    ),
                ),
            ],
            options={
                "db_table": "drop_tbl_test_table_child",
            },
        ),
        migrations.AddField(
            model_name="testtablemain",
            name="parent",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="good_flow_drop_table_with_constraints.testtableparent",
            ),
        ),
    ]
