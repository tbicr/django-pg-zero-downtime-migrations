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
                fields=["test_field_int", "test_field_str"], name="relatedtesttable_idx"
            ),
        ),
    ]
