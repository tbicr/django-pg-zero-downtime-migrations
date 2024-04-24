import re
import warnings
from contextlib import contextmanager

import django
from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.db.backends.ddl_references import Statement
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgresDatabaseSchemaEditor
)
from django.db.backends.utils import strip_quotes


class Unsafe:
    ADD_COLUMN_DEFAULT = (
        "ADD COLUMN DEFAULT is unsafe operation\n"
        "See details for safe alternative "
        "https://github.com/tbicr/django-pg-zero-downtime-migrations#create-column-with-default"
    )
    ADD_COLUMN_NOT_NULL = (
        "ADD COLUMN NOT NULL is unsafe operation\n"
        "See details for safe alternative "
        "https://github.com/tbicr/django-pg-zero-downtime-migrations#dealing-with-not-null-constraint"
    )
    ALTER_COLUMN_TYPE = (
        "ALTER COLUMN TYPE is unsafe operation\n"
        "See details for safe alternative "
        "https://github.com/tbicr/django-pg-zero-downtime-migrations#dealing-with-alter-table-alter-column-type"
    )
    ADD_CONSTRAINT_EXCLUDE = (
        "ADD CONSTRAINT EXCLUDE is unsafe operation\n"
        "See details for safe alternative "
        "https://github.com/tbicr/django-pg-zero-downtime-migrations#changes-for-working-logic"
    )
    ALTER_TABLE_RENAME = (
        "ALTER TABLE RENAME is unsafe operation\n"
        "See details for save alternative "
        "https://github.com/tbicr/django-pg-zero-downtime-migrations#changes-for-working-logic"
    )
    ALTER_TABLE_SET_TABLESPACE = (
        "ALTER TABLE SET TABLESPACE is unsafe operation\n"
        "See details for save alternative "
        "https://github.com/tbicr/django-pg-zero-downtime-migrations#changes-for-working-logic"
    )
    ALTER_TABLE_RENAME_COLUMN = (
        "ALTER TABLE RENAME COLUMN is unsafe operation\n"
        "See details for save alternative "
        "https://github.com/tbicr/django-pg-zero-downtime-migrations#changes-for-working-logic"
    )


class UnsafeOperationWarning(Warning):
    pass


class UnsafeOperationException(Exception):
    pass


class DummySQL:
    def __mod__(self, other):
        return DUMMY_SQL

    def format(self, *args, **kwargs):
        return DUMMY_SQL


DUMMY_SQL = DummySQL()


class Condition:
    def __init__(self, sql, exists, idempotent_mode_only=False):
        self.sql = sql
        self.exists = exists
        self.idempotent_mode_only = idempotent_mode_only

    def __str__(self):
        return self.sql

    def __repr__(self):
        return str(self)

    def __mod__(self, other):
        return self.__class__(
            sql=self.sql % other,
            exists=self.exists,
            idempotent_mode_only=self.idempotent_mode_only,
        )

    def format(self, *args, **kwargs):
        return self.__class__(
            sql=self.sql.format(*args, **kwargs),
            exists=self.exists,
            idempotent_mode_only=self.idempotent_mode_only,
        )


class MultiStatementSQL(list):

    def __init__(self, obj, *args):
        if args:
            obj = [obj] + list(args)
        super().__init__(obj)

    def __str__(self):
        return '\n'.join(s.rstrip(';') + ';' for s in self)

    def __repr__(self):
        return str(self)

    def __mod__(self, other):
        if other is DUMMY_SQL:
            return DUMMY_SQL
        if isinstance(other, (list, tuple)) and any(arg is DUMMY_SQL for arg in other):
            return DUMMY_SQL
        if isinstance(other, dict) and any(val is DUMMY_SQL for val in other.values()):
            return DUMMY_SQL
        return MultiStatementSQL(s % other for s in self)

    def format(self, *args, **kwargs):
        if any(arg is DUMMY_SQL for arg in args) or any(val is DUMMY_SQL for val in kwargs.values()):
            return DUMMY_SQL
        return MultiStatementSQL(s.format(*args, **kwargs) for s in self)


class PGLock:

    def __init__(
        self,
        sql,
        *,
        use_timeouts=False,
        disable_statement_timeout=False,
        idempotent_condition=None,
    ):
        self.sql = sql
        if use_timeouts and disable_statement_timeout:
            raise ValueError("Can't apply use_timeouts and disable_statement_timeout simultaneously.")
        self.use_timeouts = use_timeouts
        self.disable_statement_timeout = disable_statement_timeout
        self.idempotent_condition = idempotent_condition

    def __str__(self):
        return self.sql

    def __repr__(self):
        return str(self)

    def __mod__(self, other):
        if other is DUMMY_SQL:
            return DUMMY_SQL
        if isinstance(other, (list, tuple)) and any(arg is DUMMY_SQL for arg in other):
            return DUMMY_SQL
        if isinstance(other, dict) and any(val is DUMMY_SQL for val in other.values()):
            return DUMMY_SQL
        return self.__class__(
            self.sql % other,
            use_timeouts=self.use_timeouts,
            disable_statement_timeout=self.disable_statement_timeout,
            idempotent_condition=self.idempotent_condition % other
            if self.idempotent_condition is not None else None,
        )

    def format(self, *args, **kwargs):
        if any(arg is DUMMY_SQL for arg in args) or any(val is DUMMY_SQL for val in kwargs.values()):
            return DUMMY_SQL
        return self.__class__(
            self.sql.format(*args, **kwargs),
            use_timeouts=self.use_timeouts,
            disable_statement_timeout=self.disable_statement_timeout,
            idempotent_condition=self.idempotent_condition.format(*args, **kwargs)
            if self.idempotent_condition is not None else None,
        )


class PGAccessExclusive(PGLock):

    def __init__(
        self,
        sql,
        *,
        use_timeouts=True,
        disable_statement_timeout=False,
        idempotent_condition=None,
    ):
        super().__init__(
            sql,
            use_timeouts=use_timeouts,
            disable_statement_timeout=disable_statement_timeout,
            idempotent_condition=idempotent_condition,
        )


class PGShareUpdateExclusive(PGLock):

    def __init__(
        self,
        sql,
        *,
        use_timeouts=False,
        disable_statement_timeout=True,
        idempotent_condition=None,
    ):
        super().__init__(
            sql,
            use_timeouts=use_timeouts,
            disable_statement_timeout=disable_statement_timeout,
            idempotent_condition=idempotent_condition,
        )


class DatabaseSchemaEditorMixin:
    ZERO_TIMEOUT = '0ms'

    _sql_get_lock_timeout = "SELECT setting || unit FROM pg_settings WHERE name = 'lock_timeout'"
    _sql_get_statement_timeout = "SELECT setting || unit FROM pg_settings WHERE name = 'statement_timeout'"
    _sql_set_lock_timeout = "SET lock_timeout TO '%(lock_timeout)s'"
    _sql_set_statement_timeout = "SET statement_timeout TO '%(statement_timeout)s'"

    _sql_identity_exists = (
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = TRIM('\"' FROM '%(table)s') "
        "AND column_name = TRIM('\"' FROM '%(column)s')"
        "AND is_identity = 'YES'"
    )
    _sql_sequence_exists = "SELECT 1 FROM pg_class WHERE relname = TRIM('\"' FROM '%(name)s')"
    _sql_index_exists = "SELECT 1 FROM pg_class WHERE relname = TRIM('\"' FROM '%(name)s')"
    _sql_table_exists = "SELECT 1 FROM pg_class WHERE relname = TRIM('\"' FROM '%(table)s')"
    _sql_new_table_exists = "SELECT 1 FROM pg_class WHERE relname = TRIM('\"' FROM '%(new_table)s')"
    _sql_column_exists = (
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = TRIM('\"' FROM '%(table)s') "
        "AND column_name = TRIM('\"' FROM '%(column)s')"
    )
    _sql_new_column_exists = (
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = TRIM('\"' FROM '%(table)s') "
        "AND column_name = TRIM('\"' FROM '%(new_column)s')"
    )
    _sql_constraint_exists = (
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name = TRIM('\"' FROM '%(table)s') "
        "AND constraint_name = TRIM('\"' FROM '%(name)s')"
    )
    _sql_index_valid = (
        "SELECT 1 "
        "FROM pg_index "
        "WHERE indrelid = TRIM('\"' FROM '%(table)s')::regclass::oid "
        "AND indexrelid = TRIM('\"' FROM '%(name)s')::regclass::oid "
        "AND indisvalid"
    )
    _sql_constraint_valid = (
        "SELECT 1 "
        "FROM pg_constraint "
        "WHERE conrelid = TRIM('\"' FROM '%(table)s')::regclass::oid "
        "AND conname = TRIM('\"' FROM '%(name)s') "
        "AND convalidated"
    )

    if django.VERSION[:2] >= (4, 1):
        sql_alter_sequence_type = PGAccessExclusive(PostgresDatabaseSchemaEditor.sql_alter_sequence_type)
        sql_add_identity = PGAccessExclusive(
            PostgresDatabaseSchemaEditor.sql_add_identity,
            idempotent_condition=Condition(_sql_identity_exists, False),
        )
        sql_drop_indentity = PGAccessExclusive(PostgresDatabaseSchemaEditor.sql_drop_indentity)
    else:
        sql_alter_sequence_type = PGAccessExclusive("ALTER SEQUENCE IF EXISTS %(sequence)s AS %(type)s")
        sql_create_sequence = PGAccessExclusive(PostgresDatabaseSchemaEditor.sql_create_sequence)
        sql_set_sequence_owner = PGAccessExclusive(PostgresDatabaseSchemaEditor.sql_set_sequence_owner)
    sql_delete_sequence = PGAccessExclusive(PostgresDatabaseSchemaEditor.sql_delete_sequence)
    sql_create_table = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_create_table,
        idempotent_condition=Condition(_sql_table_exists, False),
        use_timeouts=False,
    )

    sql_delete_table = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_delete_table,
        idempotent_condition=Condition(_sql_table_exists, True),
        use_timeouts=False,
    )

    sql_rename_table = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_rename_table,
        idempotent_condition=Condition(_sql_new_table_exists, False),
    )
    sql_retablespace_table = PGAccessExclusive(PostgresDatabaseSchemaEditor.sql_retablespace_table)

    sql_create_column_inline_fk = None
    sql_create_column = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_create_column,
        idempotent_condition=Condition(_sql_column_exists, False),
    )
    sql_alter_column = PGAccessExclusive(PostgresDatabaseSchemaEditor.sql_alter_column)
    sql_delete_column = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_delete_column,
        idempotent_condition=Condition(_sql_column_exists, True),
    )
    sql_rename_column = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_rename_column,
        idempotent_condition=Condition(_sql_new_column_exists, False),
    )

    sql_create_check = MultiStatementSQL(
        PGAccessExclusive(
            "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s CHECK (%(check)s) NOT VALID",
            idempotent_condition=Condition(_sql_constraint_exists, False),
        ),
        PGShareUpdateExclusive(
            "ALTER TABLE %(table)s VALIDATE CONSTRAINT %(name)s",
            disable_statement_timeout=True,
        ),
    )
    sql_delete_check = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_delete_check,
        idempotent_condition=Condition(_sql_constraint_exists, True),
    )

    if django.VERSION[:2] >= (5, 0):
        sql_create_unique = MultiStatementSQL(
            PGShareUpdateExclusive(
                "CREATE UNIQUE INDEX CONCURRENTLY %(name)s ON %(table)s (%(columns)s)%(nulls_distinct)s",
                idempotent_condition=Condition(_sql_index_exists, False),
                disable_statement_timeout=True,
            ),
            PGShareUpdateExclusive(
                "REINDEX INDEX CONCURRENTLY %(name)s",
                idempotent_condition=Condition(_sql_index_valid, False, idempotent_mode_only=True),
                disable_statement_timeout=True,
            ),
            PGAccessExclusive(
                "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s UNIQUE USING INDEX %(name)s",
                idempotent_condition=Condition(_sql_constraint_exists, False),
            ),
        )
    else:
        sql_create_unique = MultiStatementSQL(
            PGShareUpdateExclusive(
                "CREATE UNIQUE INDEX CONCURRENTLY %(name)s ON %(table)s (%(columns)s)",
                idempotent_condition=Condition(_sql_index_exists, False),
                disable_statement_timeout=True,
            ),
            PGShareUpdateExclusive(
                "REINDEX INDEX CONCURRENTLY %(name)s",
                idempotent_condition=Condition(_sql_index_valid, False, idempotent_mode_only=True),
                disable_statement_timeout=True,
            ),
            PGAccessExclusive(
                "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s UNIQUE USING INDEX %(name)s",
                idempotent_condition=Condition(_sql_constraint_exists, False),
            ),
        )
    sql_delete_unique = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_delete_unique,
        idempotent_condition=Condition(_sql_constraint_exists, True),
    )

    sql_create_fk = MultiStatementSQL(
        PGAccessExclusive(
            "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s FOREIGN KEY (%(column)s) "
            "REFERENCES %(to_table)s (%(to_column)s)%(deferrable)s NOT VALID",
            idempotent_condition=Condition(_sql_constraint_exists, False),
        ),
        PGShareUpdateExclusive(
            "ALTER TABLE %(table)s VALIDATE CONSTRAINT %(name)s",
            disable_statement_timeout=True,
        ),
    )
    sql_delete_fk = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_delete_fk,
        idempotent_condition=Condition(_sql_constraint_exists, True),
    )

    sql_create_pk = MultiStatementSQL(
        PGShareUpdateExclusive(
            "CREATE UNIQUE INDEX CONCURRENTLY %(name)s ON %(table)s (%(columns)s)",
            idempotent_condition=Condition(_sql_index_exists, False),
            disable_statement_timeout=True,
        ),
        PGShareUpdateExclusive(
            "REINDEX INDEX CONCURRENTLY %(name)s",
            idempotent_condition=Condition(_sql_index_valid, False, idempotent_mode_only=True),
            disable_statement_timeout=True,
        ),
        PGAccessExclusive(
            "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s PRIMARY KEY USING INDEX %(name)s",
            idempotent_condition=Condition(_sql_constraint_exists, False),
        ),
    )
    sql_delete_pk = PGAccessExclusive(
        PostgresDatabaseSchemaEditor.sql_delete_pk,
        idempotent_condition=Condition(_sql_constraint_exists, True),
    )

    sql_create_index = MultiStatementSQL(
        PGShareUpdateExclusive(
            PostgresDatabaseSchemaEditor.sql_create_index_concurrently,
            idempotent_condition=Condition(_sql_index_exists, False),
            disable_statement_timeout=True,
        ),
        PGShareUpdateExclusive(
            "REINDEX INDEX CONCURRENTLY %(name)s",
            idempotent_condition=Condition(_sql_index_valid, False, idempotent_mode_only=True),
            disable_statement_timeout=True,
        ),
    )
    sql_create_index_concurrently = MultiStatementSQL(
        PGShareUpdateExclusive(
            PostgresDatabaseSchemaEditor.sql_create_index_concurrently,
            idempotent_condition=Condition(_sql_index_exists, False),
            disable_statement_timeout=True,
        ),
        PGShareUpdateExclusive(
            "REINDEX INDEX CONCURRENTLY %(name)s",
            idempotent_condition=Condition(_sql_index_valid, False, idempotent_mode_only=True),
            disable_statement_timeout=True,
        ),
    )
    if django.VERSION[:2] >= (5, 0):
        sql_create_unique_index = MultiStatementSQL(
            PGShareUpdateExclusive(
                "CREATE UNIQUE INDEX CONCURRENTLY %(name)s ON %(table)s (%(columns)s)%(condition)s%(nulls_distinct)s",
                idempotent_condition=Condition(_sql_index_exists, False),
                disable_statement_timeout=True,
            ),
            PGShareUpdateExclusive(
                "REINDEX INDEX CONCURRENTLY %(name)s",
                idempotent_condition=Condition(_sql_index_valid, False, idempotent_mode_only=True),
                disable_statement_timeout=True,
            ),
        )
    else:
        sql_create_unique_index = MultiStatementSQL(
            PGShareUpdateExclusive(
                "CREATE UNIQUE INDEX CONCURRENTLY %(name)s ON %(table)s (%(columns)s)%(condition)s",
                idempotent_condition=Condition(_sql_index_exists, False),
                disable_statement_timeout=True,
            ),
            PGShareUpdateExclusive(
                "REINDEX INDEX CONCURRENTLY %(name)s",
                idempotent_condition=Condition(_sql_index_valid, False, idempotent_mode_only=True),
                disable_statement_timeout=True,
            ),
        )
    sql_delete_index = PGShareUpdateExclusive("DROP INDEX CONCURRENTLY IF EXISTS %(name)s")
    sql_delete_index_concurrently = PGShareUpdateExclusive(
        PostgresDatabaseSchemaEditor.sql_delete_index_concurrently
    )

    if django.VERSION[:2] >= (4, 2):
        sql_alter_table_comment = PGShareUpdateExclusive(PostgresDatabaseSchemaEditor.sql_alter_table_comment)
        sql_alter_column_comment = PGShareUpdateExclusive(PostgresDatabaseSchemaEditor.sql_alter_column_comment)

    _sql_column_not_null = MultiStatementSQL(
        PGAccessExclusive(
            "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s CHECK (%(column)s IS NOT NULL) NOT VALID",
            idempotent_condition=Condition(_sql_constraint_exists, False),
        ),
        PGShareUpdateExclusive(
            "ALTER TABLE %(table)s VALIDATE CONSTRAINT %(name)s",
            disable_statement_timeout=True,
        ),
        PGAccessExclusive("ALTER TABLE %(table)s ALTER COLUMN %(column)s SET NOT NULL"),
        PGAccessExclusive(
            "ALTER TABLE %(table)s DROP CONSTRAINT %(name)s",
            idempotent_condition=Condition(_sql_constraint_exists, True),
        ),
    )

    _varchar_type_regexp = re.compile(r'^varchar\((?P<max_length>\d+)\)$')
    _numeric_type_regexp = re.compile(r'^numeric\((?P<precision>\d+), *(?P<scale>\d+)\)$')

    def __init__(self, connection, collect_sql=False, atomic=True):
        # Disable atomic transactions as it can be reason of downtime or deadlock
        # in case if you combine many operation in one migration module.
        super().__init__(connection, collect_sql=collect_sql, atomic=False)

        # Avoid using DUMMY_SQL in combined alters
        connection.features.supports_combined_alters = False

        # Get settings with defaults
        self.LOCK_TIMEOUT = getattr(settings, "ZERO_DOWNTIME_MIGRATIONS_LOCK_TIMEOUT", None)
        self.STATEMENT_TIMEOUT = getattr(settings, "ZERO_DOWNTIME_MIGRATIONS_STATEMENT_TIMEOUT", None)
        self.FLEXIBLE_STATEMENT_TIMEOUT = getattr(
            settings, "ZERO_DOWNTIME_MIGRATIONS_FLEXIBLE_STATEMENT_TIMEOUT", False)
        self.RAISE_FOR_UNSAFE = getattr(settings, "ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE", False)
        self.DEFERRED_SQL = getattr(settings, "ZERO_DOWNTIME_MIGRATIONS_DEFERRED_SQL", True)
        self.IDEMPOTENT_SQL = getattr(settings, "ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL", False)

    def execute(self, sql, params=()):
        if sql is DUMMY_SQL:
            return
        statements = []
        if isinstance(sql, MultiStatementSQL):
            statements.extend(sql)
        elif isinstance(sql, Statement) and isinstance(sql.template, MultiStatementSQL):
            statements.extend(Statement(s, **sql.parts) for s in sql.template)
        else:
            statements.append(sql)
        for statement in statements:
            idempotent_condition = None
            if isinstance(statement, PGLock):
                use_timeouts = statement.use_timeouts
                disable_statement_timeout = statement.disable_statement_timeout
                idempotent_condition = statement.idempotent_condition
                statement = statement.sql
            elif isinstance(statement, Statement) and isinstance(statement.template, PGLock):
                use_timeouts = statement.template.use_timeouts
                disable_statement_timeout = statement.template.disable_statement_timeout
                if statement.template.idempotent_condition is not None:
                    idempotent_condition = statement.template.idempotent_condition % statement.parts
                statement = Statement(statement.template.sql, **statement.parts)
            else:
                use_timeouts = False
                disable_statement_timeout = False

            if not self._skip_applied(idempotent_condition):
                if use_timeouts:
                    with self._set_operation_timeout(self.STATEMENT_TIMEOUT, self.LOCK_TIMEOUT):
                        super().execute(statement, params)
                elif disable_statement_timeout and self.FLEXIBLE_STATEMENT_TIMEOUT:
                    with self._set_operation_timeout(self.ZERO_TIMEOUT):
                        super().execute(statement, params)
                else:
                    super().execute(statement, params)

    def _skip_applied(self, idempotent_condition: Condition) -> bool:
        if idempotent_condition is None:
            return False

        if not self.IDEMPOTENT_SQL:
            # in case of failure of creating indexes concurrently index will be created but will be invalid
            # for this case reindex statement added to recreate valid index in IDEMPOTENT_SQL mode
            # but if IDEMPOTENT_SQL mode is disabled we need to skip this extra reindex sql
            return idempotent_condition.idempotent_mode_only

        with self.connection.cursor() as cursor:
            cursor.execute(idempotent_condition.sql)
            exists = cursor.fetchone() is not None
            if idempotent_condition.exists:
                return not exists
            return exists

    @contextmanager
    def _set_operation_timeout(self, statement_timeout=None, lock_timeout=None):
        if self.collect_sql:
            previous_statement_timeout = self.ZERO_TIMEOUT
            previous_lock_timeout = self.ZERO_TIMEOUT
        else:
            with self.connection.cursor() as cursor:
                cursor.execute(self._sql_get_statement_timeout)
                previous_statement_timeout, = cursor.fetchone()
                cursor.execute(self._sql_get_lock_timeout)
                previous_lock_timeout, = cursor.fetchone()
        if statement_timeout is not None:
            self.execute(self._sql_set_statement_timeout % {"statement_timeout": statement_timeout})
        if lock_timeout is not None:
            self.execute(self._sql_set_lock_timeout % {"lock_timeout": lock_timeout})
        yield
        if statement_timeout is not None:
            self.execute(self._sql_set_statement_timeout % {"statement_timeout": previous_statement_timeout})
        if lock_timeout is not None:
            self.execute(self._sql_set_lock_timeout % {"lock_timeout": previous_lock_timeout})

    def _flush_deferred_sql(self):
        """As some alternative sql use deferred sql and deferred sql run after all operations in migration module
         so good idea to run deferred sql as soon as possible to provide similar as possible state
         between operations in migration module. But this approach can be reason of errors for some migrations.

         As only constraints creation placed in deferred sql
         it looks safe to keep standard django deferred sql run approach.

         # TODO: drop option to run deferred sql as soon as possible in future
         """
        if not self.DEFERRED_SQL:
            for sql in self.deferred_sql:
                self.execute(sql)
            self.deferred_sql.clear()

    def create_model(self, model):
        super().create_model(model)
        self._flush_deferred_sql()

    def delete_model(self, model):
        super().delete_model(model)
        self._flush_deferred_sql()

    def alter_index_together(self, model, old_index_together, new_index_together):
        super().alter_index_together(model, old_index_together, new_index_together)
        self._flush_deferred_sql()

    def alter_unique_together(self, model, old_unique_together, new_unique_together):
        super().alter_unique_together(model, old_unique_together, new_unique_together)
        self._flush_deferred_sql()

    def add_index(self, model, index, concurrently=False):
        super().add_index(model, index, concurrently=concurrently)
        self._flush_deferred_sql()

    def remove_index(self, model, index, concurrently=False):
        super().remove_index(model, index, concurrently=concurrently)
        self._flush_deferred_sql()

    def add_constraint(self, model, constraint):
        if isinstance(constraint, ExclusionConstraint):
            if self.RAISE_FOR_UNSAFE:
                raise UnsafeOperationException(Unsafe.ADD_CONSTRAINT_EXCLUDE)
            else:
                warnings.warn(UnsafeOperationWarning(Unsafe.ADD_CONSTRAINT_EXCLUDE))
        super().add_constraint(model, constraint)
        self._flush_deferred_sql()

    def remove_constraint(self, model, constraint):
        super().remove_constraint(model, constraint)
        self._flush_deferred_sql()

    def add_field(self, model, field):
        super().add_field(model, field)
        self._flush_deferred_sql()

    def remove_field(self, model, field):
        super().remove_field(model, field)
        self._flush_deferred_sql()

    def alter_field(self, model, old_field, new_field, strict=False):
        super().alter_field(model, old_field, new_field, strict)
        self._flush_deferred_sql()

    def alter_db_table(self, model, old_db_table, new_db_table):
        # Disregard cases where db_table is unchanged
        if old_db_table != new_db_table:
            if self.RAISE_FOR_UNSAFE:
                raise UnsafeOperationException(Unsafe.ALTER_TABLE_RENAME)
            else:
                warnings.warn(UnsafeOperationWarning(Unsafe.ALTER_TABLE_RENAME))
        super().alter_db_table(model, old_db_table, new_db_table)
        self._flush_deferred_sql()

    def alter_db_tablespace(self, model, old_db_tablespace, new_db_tablespace):
        if self.RAISE_FOR_UNSAFE:
            raise UnsafeOperationException(Unsafe.ALTER_TABLE_SET_TABLESPACE)
        else:
            warnings.warn(UnsafeOperationWarning(Unsafe.ALTER_TABLE_SET_TABLESPACE))
        super().alter_db_tablespace(model, old_db_tablespace, new_db_tablespace)
        self._flush_deferred_sql()

    def alter_db_table_comment(self, model, old_db_table_comment, new_db_table_comment):
        super().alter_db_table_comment(model, old_db_table_comment, new_db_table_comment)
        self._flush_deferred_sql()

    def _rename_field_sql(self, table, old_field, new_field, new_type):
        if self.RAISE_FOR_UNSAFE:
            raise UnsafeOperationException(Unsafe.ALTER_TABLE_RENAME_COLUMN)
        else:
            warnings.warn(UnsafeOperationWarning(Unsafe.ALTER_TABLE_RENAME_COLUMN))
        return super()._rename_field_sql(table, old_field, new_field, new_type)

    def _add_column_default(self):
        if self.RAISE_FOR_UNSAFE:
            raise UnsafeOperationException(Unsafe.ADD_COLUMN_DEFAULT)
        else:
            warnings.warn(UnsafeOperationWarning(Unsafe.ADD_COLUMN_DEFAULT))
        return " DEFAULT %s"

    def _add_column_not_null(self, model, field):
        if self.RAISE_FOR_UNSAFE:
            raise UnsafeOperationException(Unsafe.ADD_COLUMN_NOT_NULL)
        else:
            warnings.warn(UnsafeOperationWarning(Unsafe.ADD_COLUMN_NOT_NULL))
        return " NOT NULL"

    def _add_column_primary_key(self, model, field):
        self.deferred_sql.append(self.sql_create_pk % {
            "table": self.quote_name(model._meta.db_table),
            "name": self.quote_name(self._create_index_name(model._meta.db_table, [field.column], suffix="_pk")),
            "columns": self.quote_name(field.column),
        })
        return ""

    def _add_column_unique(self, model, field):
        if django.VERSION[:2] >= (4, 0):
            self.deferred_sql.append(self._create_unique_sql(model, [field]))
        else:
            self.deferred_sql.append(self._create_unique_sql(model, [field.column]))
        return ""

    if django.VERSION[:2] <= (3, 2):
        def skip_default_on_alter(self, field):
            """
            Some backends don't accept default values for certain columns types
            (i.e. MySQL longtext and longblob) in the ALTER COLUMN statement.
            """
            return False

    def column_sql(self, model, field, include_default=False):
        """
        Take a field and return its column definition.
        The field must already have had set_attributes_from_name() called.
        """
        if not include_default:
            return super().column_sql(model, field, include_default)

        # Get the column's type and use that as the basis of the SQL
        db_params = field.db_parameters(connection=self.connection)
        sql = db_params['type']
        params = []
        # Check for fields that aren't actually columns (e.g. M2M)
        if sql is None:
            return None, None
        # Collation.
        collation = getattr(field, 'db_collation', None)
        if collation:
            sql += self._collate_sql(collation)
        # Work out nullability
        null = field.null
        # If we were told to include a default value, do so
        include_default = (
            include_default and
            not self.skip_default(field) and
            # Don't include a default value if it's a nullable field and the
            # default cannot be dropped in the ALTER COLUMN statement (e.g.
            # MySQL longtext and longblob).
            not (null and self.skip_default_on_alter(field))
        )
        if include_default:
            default_value = self.effective_default(field)
            if default_value is not None:
                sql += self._add_column_default()
                params += [default_value]
        # Oracle treats the empty string ('') as null, so coerce the null
        # option whenever '' is a possible value.
        if (field.empty_strings_allowed and not field.primary_key and
                self.connection.features.interprets_empty_strings_as_nulls):
            null = True
        if null and not self.connection.features.implied_column_null:
            sql += " NULL"
        elif not null:
            sql += self._add_column_not_null(model, field)
        # Primary key/unique outputs
        if field.primary_key:
            sql += self._add_column_primary_key(model, field)
        elif field.unique:
            sql += self._add_column_unique(model, field)
        # Optionally add the tablespace if it's an implicitly indexed column
        tablespace = field.db_tablespace or model._meta.db_tablespace
        if tablespace and self.connection.features.supports_tablespaces and field.unique:
            sql += " %s" % self.connection.ops.tablespace_sql(tablespace, inline=True)
        # Return the sql
        return sql, params

    def _alter_column_set_not_null(self, model, new_field):
        self.deferred_sql.append(self._sql_column_not_null % {
            "column": self.quote_name(new_field.column),
            "table": self.quote_name(model._meta.db_table),
            "name": self.quote_name(
                self._create_index_name(model._meta.db_table, [new_field.column], suffix="_notnull")
            ),
        })
        return DUMMY_SQL, []

    def _alter_column_drop_not_null(self, model, new_field):
        return self.sql_alter_column_null % {
            "column": self.quote_name(new_field.column),
        }, []

    def _alter_column_null_sql(self, model, old_field, new_field):
        if new_field.null:
            return self._alter_column_drop_not_null(model, new_field)
        else:
            return self._alter_column_set_not_null(model, new_field)

    def _immediate_type_cast(self, old_type, new_type):
        if (
            (old_type == new_type) or
            (old_type == 'integer' and new_type == 'serial') or
            (old_type == 'bigint' and new_type == 'bigserial') or
            (old_type == 'smallint' and new_type == 'smallserial') or
            (old_type == 'serial' and new_type == 'integer') or
            (old_type == 'bigserial' and new_type == 'bigint') or
            (old_type == 'smallserial' and new_type == 'smallint')
        ):
            return True
        old_type_varchar_match = self._varchar_type_regexp.match(old_type)
        if old_type_varchar_match:
            if new_type == "text":
                return True
            new_type_varchar_match = self._varchar_type_regexp.match(new_type)
            if new_type_varchar_match:
                old_type_max_length = int(old_type_varchar_match.group("max_length"))
                new_type_max_length = int(new_type_varchar_match.group("max_length"))
                if new_type_max_length >= old_type_max_length:
                    return True
                else:
                    return False
        old_type_numeric_match = self._numeric_type_regexp.match(old_type)
        if old_type_numeric_match:
            new_type_numeric_match = self._numeric_type_regexp.match(new_type)
            old_type_precision = int(old_type_numeric_match.group("precision"))
            old_type_scale = int(old_type_numeric_match.group("scale"))
            try:
                new_type_precision = int(new_type_numeric_match.group("precision"))
                new_type_scale = int(new_type_numeric_match.group("scale"))
            except AttributeError:
                return False
            return new_type_precision >= old_type_precision and new_type_scale == old_type_scale
        return False

    if django.VERSION[:2] < (4, 1):
        def _get_sequence_name(self, table, column):
            with self.connection.cursor() as cursor:
                for sequence in self.connection.introspection.get_sequences(cursor, table):
                    if sequence["column"] == column:
                        return sequence["name"]
            return None

    # TODO: after django 4.1 support drop replace *args, **kwargs with original signature
    def _alter_column_type_sql(self, model, old_field, new_field, new_type, *args, **kwargs):
        old_db_params = old_field.db_parameters(connection=self.connection)
        old_type = old_db_params["type"]
        if not self._immediate_type_cast(old_type, new_type):
            if self.RAISE_FOR_UNSAFE:
                raise UnsafeOperationException(Unsafe.ALTER_COLUMN_TYPE)
            else:
                warnings.warn(UnsafeOperationWarning(Unsafe.ALTER_COLUMN_TYPE))
        if django.VERSION[:2] < (4, 1):
            # old django versions runs in transaction next queries for autofield type changes:
            # - alter column type
            # - drop sequence with old type
            # - create sequence with new type
            # - alter column set default
            # - set sequence current value
            # - set sequence to field
            # if we run this queries without transaction
            # then concurrent insertions between drop sequence and end of migration can fail
            # so simplify migration to two safe steps: alter colum type and alter sequence type
            serial_fields_map = {
                "bigserial": "bigint",
                "serial": "integer",
                "smallserial": "smallint",
            }
            if new_type.lower() in serial_fields_map:
                column = strip_quotes(new_field.column)
                table = strip_quotes(model._meta.db_table)
                sequence_name = self._get_sequence_name(table, column)
                if sequence_name is not None:
                    using_sql = ""
                    if self._field_data_type(old_field) != self._field_data_type(new_field):
                        using_sql = " USING %(column)s::%(type)s"
                    return (
                        (
                            (self.sql_alter_column_type + using_sql)
                            % {
                                "column": self.quote_name(column),
                                "type": serial_fields_map[new_type.lower()],
                            },
                            [],
                        ),
                        [
                            (
                                self.sql_alter_sequence_type
                                % {
                                    "sequence": self.quote_name(sequence_name),
                                    "type": serial_fields_map[new_type.lower()],
                                },
                                [],
                            ),
                        ],
                    )
        return super()._alter_column_type_sql(model, old_field, new_field, new_type, *args, **kwargs)


class DatabaseSchemaEditor(DatabaseSchemaEditorMixin, PostgresDatabaseSchemaEditor):
    pass
