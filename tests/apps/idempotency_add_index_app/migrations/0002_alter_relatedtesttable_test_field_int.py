from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_index_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="relatedtesttable",
            name="test_field_int",
            field=models.IntegerField(db_index=True, null=True),
        ),
    ]
