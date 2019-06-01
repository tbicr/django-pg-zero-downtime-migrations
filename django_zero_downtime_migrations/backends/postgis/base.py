from django.contrib.gis.db.backends.postgis.base import (
    DatabaseWrapper as PostGISDatabaseWrapper
)

from .schema import DatabaseSchemaEditor


class DatabaseWrapper(PostGISDatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
