from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_auto_field_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="relatedtesttable",
            name="test_field_int",
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
