import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_foreign_key_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="relatedtesttable",
            name="test_field_int",
            field=models.ForeignKey(
                db_column="test_field_int",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="idempotency_add_foreign_key_app.testtable",
            ),
        ),
    ]
