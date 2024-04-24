from django.db import models


class TestTable(models.Model):
    test_field_int = models.IntegerField()
    test_field_str = models.CharField(max_length=10)


class RelatedTestTable(models.Model):
    test_model = models.ForeignKey(TestTable, null=True, on_delete=models.CASCADE)
    test_field_int = models.IntegerField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="idempotency_create_table_app_relatedtesttable_uniq",
                fields=["test_model", "test_field_int"],
            )
        ]
