from django.db import models


class TestTable(models.Model):
    test_field_int = models.IntegerField()
    test_field_str = models.CharField(max_length=10)


class RelatedTestTable(models.Model):
    test_field_int = models.IntegerField()
    test_field_str = models.CharField(max_length=10)

    class Meta:
        indexes = [
            models.Index(
                name="relatedtesttable_idx",
                fields=["test_field_int", "test_field_str"],
                condition=models.Q(test_field_int__gt=0),
            )
        ]
