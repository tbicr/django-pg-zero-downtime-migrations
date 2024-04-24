from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_index_meta_app", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="relatedtesttable",
            index=models.Index(
                condition=models.Q(("test_field_int__gt", 0)),
                fields=["test_field_int", "test_field_str"],
                name="relatedtesttable_idx",
            ),
        ),
    ]
