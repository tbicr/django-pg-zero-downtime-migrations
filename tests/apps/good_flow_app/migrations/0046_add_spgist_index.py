# Generated by Django 3.0a1 on 2019-10-14 19:49

import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('good_flow_app', '0045_drop_hash_index_with_condition'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='testtable',
            index=django.contrib.postgres.indexes.SpGistIndex(fields=['test_field_str'], name='test_index'),
        ),
    ]