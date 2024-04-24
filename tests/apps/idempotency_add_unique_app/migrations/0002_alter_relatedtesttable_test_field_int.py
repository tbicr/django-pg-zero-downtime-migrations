from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_unique_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="relatedtesttable",
            name="test_field_int",
            field=models.IntegerField(null=True, unique=True),
        ),
    ]
