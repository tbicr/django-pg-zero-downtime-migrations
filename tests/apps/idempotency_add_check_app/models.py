from django.db import models


class TestTable(models.Model):
    test_field_int = models.IntegerField()
    test_field_str = models.CharField(max_length=10)


class RelatedTestTable(models.Model):
    test_field_int = models.IntegerField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(test_field_int__gt=0),
                name="idempotency_add_check_app_relatedtesttable_check",
            )
        ]
