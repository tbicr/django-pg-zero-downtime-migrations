from django.db import models


class RelatedTestTable(models.Model):
    # the mixed case names need quotes, thus they prove that the idempotent mode
    # checks get the quoted identifier that the schema editor built
    test_field_int = models.IntegerField(null=True, unique=True, db_column='MixedCaseColumn')

    class Meta:
        db_table = 'MixedCaseIdempotency'
