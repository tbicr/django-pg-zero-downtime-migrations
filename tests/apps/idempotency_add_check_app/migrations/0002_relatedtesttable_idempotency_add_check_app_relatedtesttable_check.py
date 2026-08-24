import django
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("idempotency_add_check_app", "0001_initial"),
    ]

    if django.VERSION[:2] >= (5, 1):
        operations = [
            migrations.AddConstraint(
                model_name="relatedtesttable",
                constraint=models.CheckConstraint(
                    condition=models.Q(("test_field_int__gt", 0)),
                    name="idempotency_add_check_app_relatedtesttable_check",
                ),
            ),
        ]
    else:
        operations = [
            migrations.AddConstraint(
                model_name="relatedtesttable",
                constraint=models.CheckConstraint(
                    check=models.Q(("test_field_int__gt", 0)),
                    name="idempotency_add_check_app_relatedtesttable_check",
                ),
            ),
        ]
