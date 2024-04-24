from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RelatedTestTable",
            fields=[
                ("test_field_int", models.IntegerField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name="TestTable",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("test_field_int", models.IntegerField()),
                ("test_field_str", models.CharField(max_length=10)),
            ],
        ),
    ]
