from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_primary_key_app", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="relatedtesttable",
            name="id",
        ),
        migrations.AlterField(
            model_name="relatedtesttable",
            name="test_field_int",
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
