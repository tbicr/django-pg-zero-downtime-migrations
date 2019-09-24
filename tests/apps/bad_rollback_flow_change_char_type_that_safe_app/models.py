from django.db import models


class TestTable(models.Model):
    char_filed = models.CharField(max_length=120)
