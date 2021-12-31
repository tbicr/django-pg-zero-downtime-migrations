from django.db import models


class TestTableRenamed(models.Model):

    class Meta:
        db_table = 'test_table'
