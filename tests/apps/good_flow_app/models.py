from django.db import models


class TestTable(models.Model):
    test_field = models.IntegerField()


class RelatedTestTable(models.Model):
    pass
