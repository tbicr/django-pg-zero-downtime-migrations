from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_column_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="relatedtesttable",
            name="test_field_str",
            field=models.CharField(max_length=10, null=True),
        ),
    ]
