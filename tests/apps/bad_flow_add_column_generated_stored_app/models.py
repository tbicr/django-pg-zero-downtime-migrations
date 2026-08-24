from django.db import models


class TestTable(models.Model):
    field_int = models.IntegerField()
    field_generated = models.GeneratedField(
        expression=models.F("field_int") + models.F("field_int"),
        output_field=models.IntegerField(),
        db_persist=True,
    )
