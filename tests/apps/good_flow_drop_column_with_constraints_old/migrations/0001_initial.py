import django.db.models.deletion
import django.db.models.functions.math
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
                ("field_u2", models.IntegerField(null=True)),
                ("field_u5", models.IntegerField(null=True)),
                ("field_u7", models.IntegerField(null=True)),
                ("field_i1", models.IntegerField(null=True)),
                ("field_i2", models.IntegerField(null=True)),
                ("field_i3", models.IntegerField(null=True)),
                ("field_i4", models.IntegerField(null=True)),
                ("field_i5", models.IntegerField(null=True)),
                ("field_i6", models.IntegerField(null=True)),
                ("field_i7", models.IntegerField(null=True)),
            ],
            options={
                "db_table": "drop_col_test_table_main",
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
                "db_table": "drop_col_test_table_parent",
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
                        to="good_flow_drop_column_with_constraints_old.testtablemain",
                        to_field="main_id",
                    ),
                ),
            ],
            options={
                "db_table": "drop_col_test_table_child",
            },
        ),
        migrations.AddField(
            model_name="testtablemain",
            name="parent",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="good_flow_drop_column_with_constraints_old.testtableparent",
            ),
        ),
        migrations.AddIndex(
            model_name="testtablemain",
            index=models.Index(
                models.F("parent"), models.F("field_i1"), name="drop_col_i1"
            ),
        ),
        migrations.AddIndex(
            model_name="testtablemain",
            index=models.Index(fields=["parent", "field_i2"], name="drop_col_i2"),
        ),
        migrations.AddIndex(
            model_name="testtablemain",
            index=models.Index(
                django.db.models.functions.math.Abs("field_i3"), name="drop_col_i3"
            ),
        ),
        migrations.AddIndex(
            model_name="testtablemain",
            index=models.Index(
                models.F("parent"),
                condition=models.Q(("field_i4__gt", 0)),
                name="drop_col_i4",
            ),
        ),
        migrations.AddIndex(
            model_name="testtablemain",
            index=models.Index(
                condition=models.Q(("field_i5__gt", 0)),
                fields=["parent"],
                name="drop_col_i5",
            ),
        ),
        migrations.AddIndex(
            model_name="testtablemain",
            index=models.Index(
                models.F("parent"), include=("field_i6",), name="drop_col_i6"
            ),
        ),
        migrations.AddIndex(
            model_name="testtablemain",
            index=models.Index(
                fields=["parent"], include=("field_i7",), name="drop_col_i7"
            ),
        ),
        migrations.AddConstraint(
            model_name="testtablemain",
            constraint=models.UniqueConstraint(
                fields=("parent", "field_u2"), name="drop_col_u2"
            ),
        ),
        migrations.AddConstraint(
            model_name="testtablemain",
            constraint=models.UniqueConstraint(
                condition=models.Q(("field_u5__gt", 0)),
                fields=("parent",),
                name="drop_col_u5",
            ),
        ),
        migrations.AddConstraint(
            model_name="testtablemain",
            constraint=models.UniqueConstraint(
                fields=("parent",), include=("field_u7",), name="drop_col_u7"
            ),
        ),
    ]
