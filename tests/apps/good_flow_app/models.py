from django.db import models
from django.contrib.postgres.search import SearchVectorField


class TestTable(models.Model):
    test_field_int = models.IntegerField()
    test_field_str = models.CharField(max_length=10)
    test_field_tsv = SearchVectorField()


class RelatedTestTable(models.Model):
    pass
