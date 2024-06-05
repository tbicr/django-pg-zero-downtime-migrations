from django.db import models


class TestTableParent(models.Model):

    class Meta:
        db_table = 'drop_tbl_test_table_parent'


# class TestTableMain(models.Model):
#     parent = models.OneToOneField(TestTableParent, null=True, on_delete=models.CASCADE)
#     main_id = models.IntegerField(null=True, unique=True)
#
#     class Meta:
#         db_table = 'drop_tbl_test_table_main'


class TestTableChild(models.Model):
    # main = models.ForeignKey(TestTableMain, to_field="main_id", null=True, on_delete=models.CASCADE)

    class Meta:
        db_table = 'drop_tbl_test_table_child'
