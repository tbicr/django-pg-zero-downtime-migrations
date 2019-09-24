from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor

from django_zero_downtime_migrations.backends.postgres.schema import (
    DatabaseSchemaEditorMixin
)


class DatabaseSchemaEditor(DatabaseSchemaEditorMixin, PostGISSchemaEditor):
    pass
