from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("good_flow_drop_column_with_constraints_old", "0001_initial"),
    ]

    operations = [
        # emulate worst case untracked constraints
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # as constraint dropped with cascade or explicitly before cascade
                # we need to back untracked constraint creation to make migration revert happy
                migrations.RunSQL(
                    migrations.RunSQL.noop,
                    """
                        ALTER TABLE "drop_col_test_table_main"
                        ADD CONSTRAINT "drop_col_u2" UNIQUE ("parent_id", "field_u2");
                    """
                )
            ],
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="testtablemain",
                    name="drop_col_u2",
                ),
                migrations.RemoveConstraint(
                    model_name="testtablemain",
                    name="drop_col_u5",
                ),
                migrations.RemoveConstraint(
                    model_name="testtablemain",
                    name="drop_col_u7",
                ),
                migrations.RemoveIndex(
                    model_name="testtablemain",
                    name="drop_col_i1",
                ),
                migrations.RemoveIndex(
                    model_name="testtablemain",
                    name="drop_col_i2",
                ),
                migrations.RemoveIndex(
                    model_name="testtablemain",
                    name="drop_col_i3",
                ),
                migrations.RemoveIndex(
                    model_name="testtablemain",
                    name="drop_col_i4",
                ),
                migrations.RemoveIndex(
                    model_name="testtablemain",
                    name="drop_col_i5",
                ),
                migrations.RemoveIndex(
                    model_name="testtablemain",
                    name="drop_col_i6",
                ),
                migrations.RemoveIndex(
                    model_name="testtablemain",
                    name="drop_col_i7",
                ),
                migrations.RemoveField(
                    model_name="testtablechild",
                    name="main",
                ),
            ],
        )
    ]
