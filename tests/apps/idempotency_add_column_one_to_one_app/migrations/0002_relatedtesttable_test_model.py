import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("idempotency_add_column_one_to_one_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="relatedtesttable",
            name="test_model",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="idempotency_add_column_one_to_one_app.testtable",
            ),
        ),
    ]
