from django.db import migrations, models
from django.db.models import DB_CASCADE


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("good_flow_db_on_delete_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="relatedtesttable",
            name="test_field_int",
            field=models.ForeignKey(
                db_column="test_field_int",
                null=True,
                on_delete=DB_CASCADE,
                to="good_flow_db_on_delete_app.testtable",
            ),
        ),
    ]
