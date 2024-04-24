from django.db import models


class TestTable(models.Model):
    test_field_int = models.IntegerField()
    test_field_str = models.CharField(max_length=10)


class RelatedTestTable(models.Model):
    test_field_int = models.ForeignKey(
        TestTable,
        null=True,
        on_delete=models.CASCADE,
        db_column="test_field_int",
    )
