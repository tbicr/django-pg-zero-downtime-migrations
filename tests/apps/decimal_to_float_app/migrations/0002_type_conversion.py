from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decimal_to_float_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='value',
            name='amount',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]
