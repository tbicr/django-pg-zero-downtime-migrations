from django.db import models
from django.db.models import DB_CASCADE


class TestTable(models.Model):
    test_field_int = models.IntegerField()


class RelatedTestTable(models.Model):
    test_field_int = models.ForeignKey(
        TestTable,
        null=True,
        on_delete=DB_CASCADE,
        db_column="test_field_int",
    )
