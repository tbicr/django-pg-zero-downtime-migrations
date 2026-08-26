from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_mixed_case_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="relatedtesttable",
            name="test_field_int",
            field=models.IntegerField(db_column="MixedCaseColumn", null=True, unique=True),
        ),
    ]
