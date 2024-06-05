from django.db import models

# from django.db.models.functions import Abs


class TestTableParent(models.Model):

    class Meta:
        db_table = 'drop_col_test_table_parent'


class TestTableMain(models.Model):
    # parent = models.OneToOneField(TestTableParent, null=True, on_delete=models.CASCADE)
    # main_id = models.IntegerField(null=True, unique=True)
    # field_u2 = models.IntegerField(null=True)
    # field_u5 = models.IntegerField(null=True)
    # field_u7 = models.IntegerField(null=True)
    # field_i1 = models.IntegerField(null=True)
    # field_i2 = models.IntegerField(null=True)
    # field_i3 = models.IntegerField(null=True)
    # field_i4 = models.IntegerField(null=True)
    # field_i5 = models.IntegerField(null=True)
    # field_i6 = models.IntegerField(null=True)
    # field_i7 = models.IntegerField(null=True)

    class Meta:
        db_table = 'drop_col_test_table_main'
        # constraints = [
        #     models.UniqueConstraint(fields=["parent", "field_u2"], name="drop_col_u2"),
        #     models.UniqueConstraint(fields=["parent"], name="drop_col_u5", condition=models.Q(field_u5__gt=0)),
        #     models.UniqueConstraint(fields=["parent"], name="drop_col_u7", include=["field_u7"]),
        # ]
        # indexes = [
        #     models.Index("parent", "field_i1", name="drop_col_i1"),
        #     models.Index(fields=["parent", "field_i2"], name="drop_col_i2"),
        #     models.Index(Abs("field_i3"), name="drop_col_i3"),
        #     models.Index("parent", name="drop_col_i4", condition=models.Q(field_i4__gt=0)),
        #     models.Index(fields=["parent"], name="drop_col_i5", condition=models.Q(field_i5__gt=0)),
        #     models.Index("parent", name="drop_col_i6", include=["field_i6"]),
        #     models.Index(fields=["parent"], name="drop_col_i7", include=["field_i7"]),
        # ]


class TestTableChild(models.Model):
    # main = models.ForeignKey(TestTableMain, to_field="main_id", null=True, on_delete=models.CASCADE)

    class Meta:
        db_table = 'drop_col_test_table_child'
