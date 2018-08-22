from functools import partial

from django.db import connection, models
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as CoreDatabaseSchemaEditor
)
from django.test import override_settings

import pytest
from django_zero_downtime_migrations_postgres_backend.schema import (
    DatabaseSchemaEditor, UnsafeOperationException, UnsafeOperationWarning
)

START_TIMEOUTS = [
    'SET lock_timeout TO \'0\';',
    'SET statement_timeout TO \'0\';',
]
END_TIMEOUTS = [
    'SET lock_timeout TO \'0ms\';',
    'SET statement_timeout TO \'0ms\';',
]


def timeouts(statements):
    if isinstance(statements, str):
        statements = [statements]
    return START_TIMEOUTS + statements + END_TIMEOUTS


class Model(models.Model):
    field1 = models.IntegerField()
    field2 = models.IntegerField()


class Model2(models.Model):
    pass


schema_editor = partial(DatabaseSchemaEditor, connection=connection, collect_sql=True)


class cmp_schema_editor:
    schema_editor = DatabaseSchemaEditor
    core_schema_editor = CoreDatabaseSchemaEditor

    def __enter__(self):
        self.editor = self.schema_editor(connection=connection, collect_sql=True).__enter__()
        self.core_editor = self.core_schema_editor(connection=connection, collect_sql=True, atomic=False).__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.core_editor.__exit__(exc_type, exc_value, traceback)
        self.editor.__exit__(exc_type, exc_value, traceback)

    def __getattr__(self, item):
        self.method = item
        value = getattr(self.editor, self.method)
        if callable(value):
            return self
        return value

    def __call__(self, *args, **kwargs):
        getattr(self.core_editor, self.method)(*args, **kwargs)
        return getattr(self.editor, self.method)(*args, **kwargs)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_create_model__ok():
    with cmp_schema_editor() as editor:
        editor.create_model(Model)
    assert editor.collected_sql == editor.core_editor.collected_sql


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_drop_model__ok():
    with cmp_schema_editor() as editor:
        editor.delete_model(Model)
    assert editor.collected_sql == editor.core_editor.collected_sql


def test_rename_model__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        editor.alter_db_table(Model, 'old_name', 'new_name')
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_rename_model__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        editor.alter_db_table(Model, 'old_name', 'old_name')


def test_change_model_tablespace__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        editor.alter_db_table(Model, 'old_tablespace', 'new_tablespace')
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_change_model_tablespace__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        editor.alter_db_table(Model, 'old_tablespace', 'new_tablespace')


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_field__ok():
    with cmp_schema_editor() as editor:
        field = models.CharField(max_length=40, null=True)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


def test_add_field_with_default__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        field = models.CharField(max_length=40, default='test')
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD COLUMN "field" varchar(40) DEFAULT \'test\' NOT NULL;'
    ) + timeouts(
        'ALTER TABLE "tests_model" ALTER COLUMN "field" DROP DEFAULT;'
    )


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_field_with_default__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        field = models.CharField(max_length=40, default='test')
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)


def test_add_field_with_not_null__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        field = models.CharField(max_length=40, null=False)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_field_with_not_null__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        field = models.CharField(max_length=40, null=False)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=True)
def test_add_field_with_not_null__allowed_for_all_tables__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        field = models.CharField(max_length=40, null=False)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=10)
def test_add_field_with_not_null__allowed_for_small_tables__warning(mocker):
    mocker.patch.object(connection, 'cursor')().__enter__().fetchone.return_value = (5,)
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        field = models.CharField(max_length=40, null=False)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=1)
def test_add_field_with_not_null__use_compatible_constraint_for_large_tables__ok(mocker):
    mocker.patch.object(connection, 'cursor')().__enter__().fetchone.return_value = (5,)
    with cmp_schema_editor() as editor:
        field = models.CharField(max_length=40, null=False)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD COLUMN "field" varchar(40);',
    ) + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_notnull" '
        'CHECK ("field" IS NOT NULL) NOT VALID;',
    ) + [
        'ALTER TABLE "tests_model" VALIDATE CONSTRAINT "tests_model_field_notnull";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=False)
def test_add_field_with_not_null__use_compatible_constraint_for_all_tables__ok():
    with cmp_schema_editor() as editor:
        field = models.CharField(max_length=40, null=False)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD COLUMN "field" varchar(40);',
    ) + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_notnull" '
        'CHECK ("field" IS NOT NULL) NOT VALID;',
    ) + [
        'ALTER TABLE "tests_model" VALIDATE CONSTRAINT "tests_model_field_notnull";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_field_with_foreign_key__ok():
    with cmp_schema_editor() as editor:
        field = models.ForeignKey(Model2, null=True, on_delete=None)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD COLUMN "field_id" integer NULL;',
    ) + [
        'CREATE INDEX CONCURRENTLY "tests_model_field_id_0166400c" ON "tests_model" ("field_id");',
    ] + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_id_0166400c_fk_tests_model2_id" '
        'FOREIGN KEY ("field_id") REFERENCES "tests_model2" ("id") DEFERRABLE INITIALLY DEFERRED NOT VALID;',
    ) + [
        'ALTER TABLE "tests_model" VALIDATE CONSTRAINT "tests_model_field_id_0166400c_fk_tests_model2_id";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_field_with_primary_key__ok():
    with cmp_schema_editor() as editor:
        field = models.CharField(max_length=40, null=True, primary_key=True)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD COLUMN "field" varchar(40) NULL;',
    ) + [
        'CREATE UNIQUE INDEX CONCURRENTLY "tests_model_field_0a53d95f_pk" ON "tests_model" ("field");',
    ] + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_0a53d95f_pk" '
        'PRIMARY KEY USING INDEX "tests_model_field_0a53d95f_pk";',
    ) + [
        'CREATE INDEX CONCURRENTLY "tests_model_field_0a53d95f_like" ON "tests_model" ("field" varchar_pattern_ops);',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_field_with_unique__ok():
    with cmp_schema_editor() as editor:
        field = models.CharField(max_length=40, null=True, unique=True)
        field.set_attributes_from_name('field')
        editor.add_field(Model, field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD COLUMN "field" varchar(40) NULL;',
    ) + [
        'CREATE UNIQUE INDEX CONCURRENTLY tests_model_field_0a53d95f_uniq ON "tests_model" ("field");',
    ] + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT tests_model_field_0a53d95f_uniq '
        'UNIQUE USING INDEX tests_model_field_0a53d95f_uniq;',
    ) + [
        'CREATE INDEX CONCURRENTLY "tests_model_field_0a53d95f_like" ON "tests_model" ("field" varchar_pattern_ops);',
    ]
    # assert editor.collected_sql == TIMEOUTS + [
    #     'ALTER TABLE "tests_model" ADD COLUMN "field" varchar(40) NULL;',
    #     'CREATE UNIQUE INDEX CONCURRENTLY "tests_model_field_0a53d95f_uniq" ON "tests_model" ("field");',
    #     'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_0a53d95f_uniq" '
    #     'UNIQUE USING INDEX "tests_model_field_0a53d95f_uniq";',
    #     'CREATE INDEX CONCURRENTLY "tests_model_field_0a53d95f_like" ON "tests_model" ("field" varchar_pattern_ops);',
    # ]


def test_alter_field_varchar40_to_varchar20__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=20)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
        assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_varchar40_to_varchar20_error():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=20)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_varchar40_to_varchar80__ok():
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=80)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_varchar40_to_text__ok():
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('field')
        new_field = models.TextField()
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


def test_alter_field_decimal10_2_to_decimal5_2__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.DecimalField(max_digits=10, decimal_places=2)
        old_field.set_attributes_from_name('field')
        new_field = models.DecimalField(max_digits=5, decimal_places=2)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_decimal10_2_to_decimal5_2__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        old_field = models.DecimalField(max_digits=10, decimal_places=2)
        old_field.set_attributes_from_name('field')
        new_field = models.DecimalField(max_digits=5, decimal_places=2)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_decimal10_2_to_decimal20_2__ok():
    with cmp_schema_editor() as editor:
        old_field = models.DecimalField(max_digits=10, decimal_places=2)
        old_field.set_attributes_from_name('field')
        new_field = models.DecimalField(max_digits=20, decimal_places=2)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


def test_alter_field_decimal10_2_to_decimal10_3__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.DecimalField(max_digits=10, decimal_places=2)
        old_field.set_attributes_from_name('field')
        new_field = models.DecimalField(max_digits=10, decimal_places=3)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_decimal10_2_to_decimal10_3__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        old_field = models.DecimalField(max_digits=10, decimal_places=2)
        old_field.set_attributes_from_name('field')
        new_field = models.DecimalField(max_digits=10, decimal_places=3)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)


def test_alter_field_decimal10_2_to_decimal10_1__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.DecimalField(max_digits=10, decimal_places=2)
        old_field.set_attributes_from_name('field')
        new_field = models.DecimalField(max_digits=10, decimal_places=1)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_decimal10_2_to_decimal10_1__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        old_field = models.DecimalField(max_digits=10, decimal_places=2)
        old_field.set_attributes_from_name('field')
        new_field = models.DecimalField(max_digits=10, decimal_places=1)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)


def test_alter_field_set_not_null__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.CharField(max_length=40, null=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=False)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_set_not_null__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        old_field = models.CharField(max_length=40, null=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=False)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=True)
def test_alter_field_set_not_null__allowed_for_all_tables__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.CharField(max_length=40, null=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=False)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=10)
def test_alter_field_set_not_null__allowed_for_small_tables__warning(mocker):
    mocker.patch.object(connection, 'cursor')().__enter__().fetchone.return_value = (5,)
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.CharField(max_length=40, null=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=False)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=1)
def test_alter_field_set_not_null__use_compatible_constraint_for_large_tables__ok(mocker):
    mocker.patch.object(connection, 'cursor')().__enter__().fetchone.return_value = (5,)
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, null=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=False)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_0a53d95f_notnull" '
        'CHECK ("field" IS NOT NULL) NOT VALID;',
    ) + [
        'ALTER TABLE "tests_model" VALIDATE CONSTRAINT "tests_model_field_0a53d95f_notnull";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=False)
def test_alter_field_set_not_null__use_compatible_constraint_for_all_tables__ok():
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, null=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=False)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_0a53d95f_notnull" '
        'CHECK ("field" IS NOT NULL) NOT VALID;',
    ) + [
        'ALTER TABLE "tests_model" VALIDATE CONSTRAINT "tests_model_field_0a53d95f_notnull";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_filed_drop_not_null__ok(mocker):
    mocker.patch.object(connection, 'cursor')().__enter__().fetchone.return_value = None
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, null=False)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=True)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_filed_drop_not_null_constraint__ok(mocker):
    mocker.patch.object(connection, 'cursor')().__enter__().fetchone.return_value = (
        'tests_model_field_0a53d95f_notnull',
    )
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, null=False)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, null=True)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" DROP CONSTRAINT tests_model_field_0a53d95f_notnull;',
    )


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_set_default__ok():
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, default='test')
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    # no sql executed because django doesn't use database defaults
    assert editor.collected_sql == editor.core_editor.collected_sql


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_drop_default__ok():
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, default='test')
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    # no sql executed because django doesn't use database defaults
    assert editor.collected_sql == editor.core_editor.collected_sql


def test_rename_field__warning():
    with cmp_schema_editor() as editor, pytest.warns(UnsafeOperationWarning):
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('old_field')
        new_field = models.CharField(max_length=40)
        new_field.set_attributes_from_name('new_field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_rename_field__raise():
    with cmp_schema_editor() as editor, pytest.raises(UnsafeOperationException):
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('old_field')
        new_field = models.CharField(max_length=40)
        new_field.set_attributes_from_name('new_field')
        editor.alter_field(Model, old_field, new_field)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_remove_field__ok():
    with cmp_schema_editor() as editor:
        field = models.CharField(max_length=40)
        field.set_attributes_from_name('field')
        editor.remove_field(Model, field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_add_constraint_check__ok():
    with cmp_schema_editor() as editor:
        old_field = models.IntegerField()
        old_field.set_attributes_from_name('field')
        new_field = models.PositiveIntegerField()
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_0a53d95f_check" '
        'CHECK ("field" >= 0) NOT VALID;',
    ) + [
        'ALTER TABLE "tests_model" VALIDATE CONSTRAINT "tests_model_field_0a53d95f_check";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_drop_constraint_check__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    mocker.patch.object(connection.introspection, 'get_constraints').return_value = {
        'tests_model_field_0a53d95f_check': {
            'columns': ['field'],
            'primary_key': False,
            'unique': False,
            'foreign_key': None,
            'check': True,
            'index': False,
            'definition': None,
            'options': None,
        }
    }
    with cmp_schema_editor() as editor:
        old_field = models.PositiveIntegerField()
        old_field.set_attributes_from_name('field')
        new_field = models.IntegerField()
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_filed_add_constraint_foreign_key__ok():
    with cmp_schema_editor() as editor:
        old_field = models.IntegerField()
        old_field.set_attributes_from_name('field_id')
        new_field = models.ForeignKey(Model2, on_delete=None)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == [
        'CREATE INDEX CONCURRENTLY "tests_model_field_id_0166400c" ON "tests_model" ("field_id");',
    ] + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_id_0166400c_fk_tests_model2_id" '
        'FOREIGN KEY ("field_id") REFERENCES "tests_model2" ("id") DEFERRABLE INITIALLY DEFERRED NOT VALID;',
    ) + [
        'ALTER TABLE "tests_model" VALIDATE CONSTRAINT "tests_model_field_id_0166400c_fk_tests_model2_id";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_drop_constraint_foreign_key__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    mocker.patch.object(connection.introspection, 'get_constraints').return_value = {
        'tests_model_field_0a53d95f_pk': {
            'columns': ['field_id'],
            'primary_key': False,
            'unique': False,
            'foreign_key': (Model2._meta.db_table, 'id'),
            'check': False,
            'index': False,
            'definition': None,
            'options': None,
        }
    }
    with cmp_schema_editor() as editor:
        old_field = models.ForeignKey(Model2, on_delete=None)
        old_field.set_attributes_from_name('field')
        new_field = models.IntegerField()
        new_field.set_attributes_from_name('field_id')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_add_constraint_primary_key__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, unique=True)
        old_field.set_attributes_from_name('field')
        old_field.model = Model
        new_field = models.CharField(max_length=40, primary_key=True)
        new_field.set_attributes_from_name('field')
        new_field.model = Model
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == [
        'CREATE UNIQUE INDEX CONCURRENTLY "tests_model_field_0a53d95f_pk" ON "tests_model" ("field");',
    ] + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_0a53d95f_pk" '
        'PRIMARY KEY USING INDEX "tests_model_field_0a53d95f_pk";',
    )


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_drop_constraint_primary_key__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    mocker.patch.object(connection.introspection, 'get_constraints').return_value = {
        'tests_model_field_0a53d95f_pk': {
            'columns': ['field'],
            'primary_key': True,
            'unique': True,
            'foreign_key': None,
            'check': False,
            'index': False,
            'definition': None,
            'options': None,
        }
    }
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, primary_key=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" DROP CONSTRAINT "tests_model_field_0a53d95f_pk";',
    ) + [
        'DROP INDEX CONCURRENTLY IF EXISTS "tests_model_field_0a53d95f_like";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_add_constraint_unique__ok():
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, unique=True)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == [
        'CREATE UNIQUE INDEX CONCURRENTLY tests_model_field_0a53d95f_uniq ON "tests_model" ("field");',
    ] + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT tests_model_field_0a53d95f_uniq '
        'UNIQUE USING INDEX tests_model_field_0a53d95f_uniq;',
    ) + [
        'CREATE INDEX CONCURRENTLY "tests_model_field_0a53d95f_like" ON "tests_model" ("field" varchar_pattern_ops);',
    ]
    # assert editor.collected_sql == TIMEOUTS + [
    #     'CREATE UNIQUE INDEX CONCURRENTLY "tests_model_field_0a53d95f_uniq" ON "tests_model" ("field");',
    #     'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field_0a53d95f_uniq" '
    #     'UNIQUE USING INDEX "tests_model_field_0a53d95f_uniq";',
    #     'CREATE INDEX CONCURRENTLY "tests_model_field_0a53d95f_like" ON "tests_model" ("field" varchar_pattern_ops);',
    # ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_alter_field_drop_constraint_unique__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    mocker.patch.object(connection.introspection, 'get_constraints').return_value = {
        'tests_model_field_0a53d95f_uniq': {
            'columns': ['field'],
            'primary_key': False,
            'unique': True,
            'foreign_key': None,
            'check': False,
            'index': False,
            'definition': None,
            'options': None,
        }
    }
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, unique=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == timeouts(
        'ALTER TABLE "tests_model" DROP CONSTRAINT "tests_model_field_0a53d95f_uniq";',
    ) + [
        'DROP INDEX CONCURRENTLY IF EXISTS "tests_model_field_0a53d95f_like";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_index__ok():
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40, db_index=True)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == [
        'CREATE INDEX CONCURRENTLY "tests_model_field_0a53d95f" ON "tests_model" ("field");',
        'CREATE INDEX CONCURRENTLY "tests_model_field_0a53d95f_like" ON "tests_model" ("field" varchar_pattern_ops);',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_remove_index__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    mocker.patch.object(connection.introspection, 'get_constraints').return_value = {
        'tests_model_field_idx': {
            'columns': ['field'],
            'orders': ['ASC'],
            'primary_key': False,
            'unique': False,
            'foreign_key': None,
            'check': False,
            'index': True,
            'type': 'idx',
            'definition': None,
            'options': None,
        }
    }
    with cmp_schema_editor() as editor:
        old_field = models.CharField(max_length=40, db_index=True)
        old_field.set_attributes_from_name('field')
        new_field = models.CharField(max_length=40)
        new_field.set_attributes_from_name('field')
        editor.alter_field(Model, old_field, new_field)
    assert editor.collected_sql == [
        'DROP INDEX CONCURRENTLY IF EXISTS "tests_model_field_idx";',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_unique_together__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    with cmp_schema_editor() as editor:
        editor.alter_unique_together(Model, [], [['field1', 'field2']])
    assert editor.collected_sql == [
        'CREATE UNIQUE INDEX CONCURRENTLY tests_model_field1_field2_51878e08_uniq '
        'ON "tests_model" ("field1", "field2");',
    ] + timeouts(
        'ALTER TABLE "tests_model" ADD CONSTRAINT tests_model_field1_field2_51878e08_uniq '
        'UNIQUE USING INDEX tests_model_field1_field2_51878e08_uniq;',
    )
    # assert editor.collected_sql == TIMEOUTS + [
    #     'CREATE UNIQUE INDEX CONCURRENTLY "tests_model_field1_field2_51878e08_uniq" '
    #     'ON "tests_model" ("field1", "field2");',
    #     'ALTER TABLE "tests_model" ADD CONSTRAINT "tests_model_field1_field2_51878e08_uniq" '
    #     'UNIQUE USING INDEX "tests_model_field1_field2_51878e08_uniq";',
    # ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_remove_unique_together__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    mocker.patch.object(connection.introspection, 'get_constraints').return_value = {
        'tests_model_field_idx': {
            'columns': ['field1', 'field2'],
            'primary_key': False,
            'unique': True,
            'foreign_key': None,
            'check': False,
            'index': False,
            'definition': None,
            'options': None,
        }
    }
    with cmp_schema_editor() as editor:
        editor.alter_unique_together(Model, [['field1', 'field2']], [])
    assert editor.collected_sql == timeouts(editor.core_editor.collected_sql)


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_add_index_together__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    with cmp_schema_editor() as editor:
        editor.alter_index_together(Model, [], [['field1', 'field2']])
    assert editor.collected_sql == [
        'CREATE INDEX CONCURRENTLY "tests_model_field1_field2_51878e08_idx" '
        'ON "tests_model" ("field1", "field2");',
    ]


@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_remove_index_together__ok(mocker):
    mocker.patch.object(connection, 'cursor')
    mocker.patch.object(connection.introspection, 'get_constraints').return_value = {
        'tests_model_field_idx': {
            'columns': ['field1', 'field2'],
            'orders': ['ASC', 'ASC'],
            'primary_key': False,
            'unique': False,
            'foreign_key': None,
            'check': False,
            'index': True,
            'type': 'idx',
            'definition': None,
            'options': None,
        }
    }
    with cmp_schema_editor() as editor:
        editor.alter_index_together(Model, [['field1', 'field2']], [])
    assert editor.collected_sql == [
        'DROP INDEX CONCURRENTLY IF EXISTS "tests_model_field_idx";',
    ]
