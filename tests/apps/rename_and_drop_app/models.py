from django.db import models


class TestTable(models.Model):
    test_field_int = models.IntegerField()

    class Meta:
        db_table = "rename_and_drop_test_table_new"
