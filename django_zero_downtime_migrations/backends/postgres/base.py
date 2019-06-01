from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper
)

from .schema import DatabaseSchemaEditor


class DatabaseWrapper(PostgresDatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
