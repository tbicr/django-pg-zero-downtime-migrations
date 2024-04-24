from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_check_app", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="relatedtesttable",
            constraint=models.CheckConstraint(
                check=models.Q(("test_field_int__gt", 0)),
                name="idempotency_add_check_app_relatedtesttable_check",
            ),
        ),
    ]
