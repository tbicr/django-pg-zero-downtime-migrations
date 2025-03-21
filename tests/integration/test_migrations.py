import os
import textwrap

import django
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.test import modify_settings, override_settings

import pytest

from django_zero_downtime_migrations.backends.postgres.schema import (
    UnsafeOperationException
)
from tests import skip_for_default_django_backend
from tests.integration import (
    is_valid_constraint, is_valid_index, make_index_invalid, one_line_sql,
    pg_dump, split_sql_queries
)


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.good_flow_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True,
                   ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_sqlmigrate_with_idempotent_mode():
    app_config = apps.get_app_config("good_flow_app")
    for migration in os.listdir(os.path.join(app_config.path, "migrations")):
        if not migration.startswith("_") and migration.endswith(".py"):
            call_command("sqlmigrate", "good_flow_app", migration[:4])


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.good_flow_alter_table_with_same_db_table"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow_alter_table_with_same_db_table():
    # forward
    call_command("migrate", "good_flow_alter_table_with_same_db_table")

    # backward
    call_command("migrate", "good_flow_alter_table_with_same_db_table", "zero")


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.good_flow_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow():
    # forward
    call_command("migrate", "good_flow_app")

    # backward
    call_command("migrate", "good_flow_app", "zero")


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.good_flow_app_concurrently"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow_create_and_drop_index_concurrently():
    # forward
    call_command("migrate", "good_flow_app_concurrently")

    # backward
    call_command("migrate", "good_flow_app_concurrently", "zero")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.bad_rollback_flow_drop_column_with_notnull_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_rollback_flow_drop_column_with_notnull():
    # forward
    call_command("migrate", "bad_rollback_flow_drop_column_with_notnull_app")

    # backward
    with pytest.raises(UnsafeOperationException):
        call_command("migrate", "bad_rollback_flow_drop_column_with_notnull_app", "0001")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.bad_rollback_flow_drop_column_with_notnull_default_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_rollback_flow_drop_column_with_notnull_default():
    # forward
    call_command("migrate", "bad_rollback_flow_drop_column_with_notnull_default_app")

    # backward
    with pytest.raises(UnsafeOperationException):
        call_command("migrate", "bad_rollback_flow_drop_column_with_notnull_default_app", "0001")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.bad_rollback_flow_change_char_type_that_safe_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_rollback_flow_change_char_type_that_safe():
    # forward
    call_command("migrate", "bad_rollback_flow_change_char_type_that_safe_app")

    # backward
    with pytest.raises(UnsafeOperationException):
        call_command("migrate", "bad_rollback_flow_change_char_type_that_safe_app", "0001")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.bad_flow_add_column_with_default_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_add_column_with_default():
    # forward
    with pytest.raises(UnsafeOperationException):
        call_command("migrate", "bad_flow_add_column_with_default_app")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.bad_flow_add_column_with_notnull_default_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_add_column_with_notnull_default():
    # forward
    with pytest.raises(UnsafeOperationException):
        call_command("migrate", "bad_flow_add_column_with_notnull_default_app")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.bad_flow_add_column_with_notnull_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_add_column_with_notnull():
    # forward
    with pytest.raises(UnsafeOperationException):
        call_command("migrate", "bad_flow_add_column_with_notnull_app")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.bad_flow_change_char_type_that_unsafe_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_change_char_type_that_unsafe():
    # forward
    with pytest.raises(UnsafeOperationException):
        call_command("migrate", "bad_flow_change_char_type_that_unsafe_app")


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.decimal_to_float_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False)
def test_decimal_to_float_app():
    # forward
    call_command("migrate", "decimal_to_float_app")

    # backward
    call_command("migrate", "decimal_to_float_app", "zero")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.good_flow_drop_table_with_constraints"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow_drop_table_with_constraints():
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_EXPLICIT_CONSTRAINTS_DROP=False):
        call_command("migrate", "good_flow_drop_table_with_constraints")
    drop_tbl_test_table_parent_schema = pg_dump("drop_tbl_test_table_parent")
    drop_tbl_test_table_child_schema = pg_dump("drop_tbl_test_table_child")
    call_command("migrate", "good_flow_drop_table_with_constraints", "zero")

    _drop_child_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "drop_tbl_test_table__main_id_8a4874b6_fk_drop_tbl_" IMMEDIATE;
        ALTER TABLE "drop_tbl_test_table_child"
        DROP CONSTRAINT "drop_tbl_test_table__main_id_8a4874b6_fk_drop_tbl_";
    """)
    _drop_main_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "drop_tbl_test_table__parent_id_5c6ff8d9_fk_drop_tbl_" IMMEDIATE;
        ALTER TABLE "drop_tbl_test_table_main"
        DROP CONSTRAINT "drop_tbl_test_table__parent_id_5c6ff8d9_fk_drop_tbl_";
    """)
    _drop_table_sql = one_line_sql("""
        DROP TABLE "drop_tbl_test_table_main" CASCADE;
    """)

    call_command("migrate", "good_flow_drop_table_with_constraints", "0002")
    migration_sql = call_command("sqlmigrate", "good_flow_drop_table_with_constraints", "0003")
    assert split_sql_queries(migration_sql) == [
        _drop_child_foreign_key_constraint_sql,
        _drop_main_foreign_key_constraint_sql,
        _drop_table_sql,
    ]
    call_command("migrate", "good_flow_drop_table_with_constraints")
    assert pg_dump("drop_tbl_test_table_parent") == drop_tbl_test_table_parent_schema
    assert pg_dump("drop_tbl_test_table_child") == drop_tbl_test_table_child_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.good_flow_drop_column_with_constraints"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow_drop_column_with_constraints():
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_EXPLICIT_CONSTRAINTS_DROP=False):
        call_command("migrate", "good_flow_drop_column_with_constraints")
    drop_col_test_table_parent_schema = pg_dump("drop_col_test_table_parent")
    drop_col_test_table_main_schema = pg_dump("drop_col_test_table_main")
    drop_col_test_table_child_schema = pg_dump("drop_col_test_table_child")
    call_command("migrate", "good_flow_drop_column_with_constraints", "zero")

    call_command("migrate", "good_flow_drop_column_with_constraints", "0002")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0003")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i7";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i7" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0003")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0004")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i6";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i6" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0004")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0005")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i5";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i5" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0005")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0006")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i4";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i4" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0006")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0007")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i3";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i3" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0007")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0008")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i2";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i2" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0008")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0009")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i1";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i1" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0009")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0010")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u7";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u7" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0010")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0011")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u6";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u6" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0011")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0012")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u5";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u5" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0012")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0013")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u4";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u4" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0013")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0014")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u3";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u3" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0014")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0015")
    assert split_sql_queries(migration_sql) == [
        'ALTER TABLE "drop_col_test_table_main" DROP CONSTRAINT "drop_col_u2";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u2" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0015")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0016")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u1";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u1" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0016")

    _drop_main_id_child_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "drop_col_test_table__main_id_9da91a1c_fk_drop_col_" IMMEDIATE;
        ALTER TABLE "drop_col_test_table_child"
        DROP CONSTRAINT "drop_col_test_table__main_id_9da91a1c_fk_drop_col_";
    """)
    _drop_main_id_field_unique_constraint = one_line_sql("""
        ALTER TABLE "drop_col_test_table_main"
        DROP CONSTRAINT "drop_col_test_table_main_main_id_key";
    """)
    _drop_main_id_column_sql = one_line_sql("""
        ALTER TABLE "drop_col_test_table_main" DROP COLUMN "main_id" CASCADE;
    """)
    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0017")
    assert split_sql_queries(migration_sql) == [
        _drop_main_id_child_foreign_key_constraint_sql,
        _drop_main_id_field_unique_constraint,
        _drop_main_id_column_sql,
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0017")

    _drop_parent_id_main_foreign_key_constraint_sql = one_line_sql("""
         SET CONSTRAINTS "drop_col_test_table__parent_id_55b0b5e6_fk_drop_col_" IMMEDIATE;
         ALTER TABLE "drop_col_test_table_main"
         DROP CONSTRAINT "drop_col_test_table__parent_id_55b0b5e6_fk_drop_col_";
     """)
    _drop_parent_id_field_unique_constraint = one_line_sql("""
         ALTER TABLE "drop_col_test_table_main"
         DROP CONSTRAINT "drop_col_test_table_main_parent_id_55b0b5e6_uniq";
     """)
    _drop_parent_id_column_sql = one_line_sql("""
         ALTER TABLE "drop_col_test_table_main" DROP COLUMN "parent_id" CASCADE;
     """)
    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints", "0018")
    assert split_sql_queries(migration_sql) == [
        _drop_parent_id_main_foreign_key_constraint_sql,
        _drop_parent_id_field_unique_constraint,
        _drop_parent_id_column_sql,
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints", "0018")

    call_command("migrate", "good_flow_drop_column_with_constraints")
    assert pg_dump("drop_col_test_table_parent") == drop_col_test_table_parent_schema
    assert pg_dump("drop_col_test_table_main") == drop_col_test_table_main_schema
    assert pg_dump("drop_col_test_table_child") == drop_col_test_table_child_schema


@skip_for_default_django_backend
@pytest.mark.skipif(
    django.VERSION[:2] >= (4, 0),
    reason="django after 4.0 case",
)
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.good_flow_drop_column_with_constraints_old"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow_drop_column_with_constraints_old():
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_EXPLICIT_CONSTRAINTS_DROP=False):
        call_command("migrate", "good_flow_drop_column_with_constraints_old")
    drop_col_test_table_parent_schema = pg_dump("drop_col_test_table_parent")
    drop_col_test_table_main_schema = pg_dump("drop_col_test_table_main")
    drop_col_test_table_child_schema = pg_dump("drop_col_test_table_child")
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "zero")

    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0002")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0003")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i7";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i7" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0003")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0004")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i6";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i6" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0004")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0005")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i5";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i5" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0005")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0006")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i4";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i4" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0006")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0007")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i3";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i3" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0007")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0008")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i2";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i2" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0008")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0009")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_i1";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_i1" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0009")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0010")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u7";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u7" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0010")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0011")
    assert split_sql_queries(migration_sql) == [
        'DROP INDEX CONCURRENTLY IF EXISTS "drop_col_u5";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u5" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0011")

    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0012")
    assert split_sql_queries(migration_sql) == [
        'ALTER TABLE "drop_col_test_table_main" DROP CONSTRAINT "drop_col_u2";',
        'ALTER TABLE "drop_col_test_table_main" DROP COLUMN "field_u2" CASCADE;',
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0012")

    _drop_main_id_child_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "drop_col_test_table__main_id_9da91a1c_fk_drop_col_" IMMEDIATE;
        ALTER TABLE "drop_col_test_table_child"
        DROP CONSTRAINT "drop_col_test_table__main_id_9da91a1c_fk_drop_col_";
    """)
    _drop_main_id_field_unique_constraint = one_line_sql("""
        ALTER TABLE "drop_col_test_table_main"
        DROP CONSTRAINT "drop_col_test_table_main_main_id_key";
    """)
    _drop_main_id_column_sql = one_line_sql("""
        ALTER TABLE "drop_col_test_table_main" DROP COLUMN "main_id" CASCADE;
    """)
    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0013")
    assert split_sql_queries(migration_sql) == [
        _drop_main_id_child_foreign_key_constraint_sql,
        _drop_main_id_field_unique_constraint,
        _drop_main_id_column_sql,
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0013")

    _drop_parent_id_main_foreign_key_constraint_sql = one_line_sql("""
         SET CONSTRAINTS "drop_col_test_table__parent_id_55b0b5e6_fk_drop_col_" IMMEDIATE;
         ALTER TABLE "drop_col_test_table_main"
         DROP CONSTRAINT "drop_col_test_table__parent_id_55b0b5e6_fk_drop_col_";
     """)
    _drop_parent_id_field_unique_constraint = one_line_sql("""
         ALTER TABLE "drop_col_test_table_main"
         DROP CONSTRAINT "drop_col_test_table_main_parent_id_55b0b5e6_uniq";
     """)
    _drop_parent_id_column_sql = one_line_sql("""
         ALTER TABLE "drop_col_test_table_main" DROP COLUMN "parent_id" CASCADE;
     """)
    migration_sql = call_command("sqlmigrate", "good_flow_drop_column_with_constraints_old", "0014")
    assert split_sql_queries(migration_sql) == [
        _drop_parent_id_main_foreign_key_constraint_sql,
        _drop_parent_id_field_unique_constraint,
        _drop_parent_id_column_sql,
    ]
    call_command("migrate", "good_flow_drop_column_with_constraints_old", "0014")

    call_command("migrate", "good_flow_drop_column_with_constraints_old")
    assert pg_dump("drop_col_test_table_parent") == drop_col_test_table_parent_schema
    assert pg_dump("drop_col_test_table_main") == drop_col_test_table_main_schema
    assert pg_dump("drop_col_test_table_child") == drop_col_test_table_child_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_create_table_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_create_table():
    _create_table_sql = one_line_sql("""
        CREATE TABLE "idempotency_create_table_app_relatedtesttable" (
            "id" integer NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            "test_field_int" integer NULL,
            "test_model_id" integer NULL
        );
    """)
    _create_unique_index_sql = one_line_sql("""
        CREATE UNIQUE INDEX CONCURRENTLY "idempotency_create_table_app_relatedtesttable_uniq"
        ON "idempotency_create_table_app_relatedtesttable" ("test_model_id", "test_field_int");
    """)
    _create_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_create_table_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_create_table_app_relatedtesttable_uniq"
        UNIQUE USING INDEX "idempotency_create_table_app_relatedtesttable_uniq";
    """)
    _create_foreign_key_sql = one_line_sql("""
        ALTER TABLE "idempotency_create_table_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_create_t_test_model_id_09b52f79_fk_idempoten"
        FOREIGN KEY ("test_model_id")
        REFERENCES "idempotency_create_table_app_testtable" ("id")
        DEFERRABLE INITIALLY DEFERRED NOT VALID;
    """)
    _validate_foreign_key_sql = one_line_sql("""
        ALTER TABLE "idempotency_create_table_app_relatedtesttable"
        VALIDATE CONSTRAINT "idempotency_create_t_test_model_id_09b52f79_fk_idempoten";
    """)
    _create_index_sql = one_line_sql("""
        CREATE INDEX CONCURRENTLY "idempotency_create_table_a_test_model_id_09b52f79"
        ON "idempotency_create_table_app_relatedtesttable" ("test_model_id");
    """)

    _drop_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_create_table_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_create_table_app_relatedtesttable_uniq";
    """)
    _drop_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "idempotency_create_t_test_model_id_09b52f79_fk_idempoten" IMMEDIATE;
        ALTER TABLE "idempotency_create_table_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_create_t_test_model_id_09b52f79_fk_idempoten";
    """)
    _drop_table_sql = one_line_sql("""
        DROP TABLE "idempotency_create_table_app_relatedtesttable" CASCADE;
    """)

    # get target schema
    call_command("migrate", "idempotency_create_table_app", "0001")
    call_command("migrate", "idempotency_create_table_app")
    new_schema = pg_dump("idempotency_create_table_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_create_table_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_create_table_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_table_sql,
        _create_unique_index_sql,
        _create_unique_constraint_sql,
        _create_foreign_key_sql,
        _validate_foreign_key_sql,
        _create_index_sql,
    ]

    # migrate case 1
    call_command("migrate", "idempotency_create_table_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_table_sql)
    call_command("migrate", "idempotency_create_table_app")
    assert pg_dump("idempotency_create_table_app_relatedtesttable") == new_schema

    # migrate case 2.1
    call_command("migrate", "idempotency_create_table_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_table_sql)
        cursor.execute(_create_unique_index_sql)
    assert is_valid_index(
        "idempotency_create_table_app_relatedtesttable",
        "idempotency_create_table_app_relatedtesttable_uniq",
    )
    call_command("migrate", "idempotency_create_table_app")
    assert pg_dump("idempotency_create_table_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_create_table_app_relatedtesttable",
        "idempotency_create_table_app_relatedtesttable_uniq",
    )

    # migrate case 2.2
    call_command("migrate", "idempotency_create_table_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_table_sql)
        cursor.execute(_create_unique_index_sql)
    make_index_invalid(
        "idempotency_create_table_app_relatedtesttable",
        "idempotency_create_table_app_relatedtesttable_uniq",
    )
    call_command("migrate", "idempotency_create_table_app")
    assert pg_dump("idempotency_create_table_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_create_table_app_relatedtesttable",
        "idempotency_create_table_app_relatedtesttable_uniq",
    )

    # migrate case 3
    call_command("migrate", "idempotency_create_table_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_table_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
    call_command("migrate", "idempotency_create_table_app")
    assert pg_dump("idempotency_create_table_app_relatedtesttable") == new_schema

    # migrate case 4
    call_command("migrate", "idempotency_create_table_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_table_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
        cursor.execute(_create_foreign_key_sql)
    call_command("migrate", "idempotency_create_table_app")
    assert pg_dump("idempotency_create_table_app_relatedtesttable") == new_schema

    # migrate case 5
    call_command("migrate", "idempotency_create_table_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_table_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
        cursor.execute(_create_foreign_key_sql)
        cursor.execute(_validate_foreign_key_sql)
    call_command("migrate", "idempotency_create_table_app")
    assert pg_dump("idempotency_create_table_app_relatedtesttable") == new_schema

    # migrate case 6
    call_command("migrate", "idempotency_create_table_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_table_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
        cursor.execute(_create_foreign_key_sql)
        cursor.execute(_validate_foreign_key_sql)
        cursor.execute(_create_index_sql)
    call_command("migrate", "idempotency_create_table_app")
    assert pg_dump("idempotency_create_table_app_relatedtesttable") == new_schema

    # rollback (covers drop table case)
    call_command("migrate", "idempotency_create_table_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_create_table_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_unique_constraint_sql,
        _drop_foreign_key_constraint_sql,
        _drop_table_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_create_table_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_unique_constraint_sql)
    call_command("migrate", "idempotency_create_table_app", "0001")

    # rollback case 2
    call_command("migrate", "idempotency_create_table_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_unique_constraint_sql)
        cursor.execute(_drop_table_sql)
    call_command("migrate", "idempotency_create_table_app", "0001")


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_column_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_column():
    _add_column_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_app_relatedtesttable"
        ADD COLUMN "test_field_str" varchar(10) NULL;
    """)

    _drop_column_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_app_relatedtesttable"
        DROP COLUMN "test_field_str" CASCADE;
    """)

    # get target schema
    call_command("migrate", "idempotency_add_column_app", "0001")
    old_schema = pg_dump("idempotency_add_column_app_relatedtesttable")
    call_command("migrate", "idempotency_add_column_app")
    new_schema = pg_dump("idempotency_add_column_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_column_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_column_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _add_column_sql
    ]

    # migrate case 1
    call_command("migrate", "idempotency_add_column_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
    call_command("migrate", "idempotency_add_column_app")
    assert pg_dump("idempotency_add_column_app_relatedtesttable") == new_schema

    # rollback (covers drop column case)
    call_command("migrate", "idempotency_add_column_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_column_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_column_sql
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_column_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_column_sql)
    call_command("migrate", "idempotency_add_column_app", "0001")
    assert pg_dump("idempotency_add_column_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_column_foreign_key_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_column_foreign_key():
    _add_column_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_foreign_key_app_relatedtesttable"
        ADD COLUMN "test_model_id" integer NULL;
    """)
    _create_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_foreign_key_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_colu_test_model_id_99eba75b_fk_idempoten"
        FOREIGN KEY ("test_model_id")
        REFERENCES "idempotency_add_column_foreign_key_app_testtable" ("id")
        DEFERRABLE INITIALLY DEFERRED NOT VALID;
    """)
    _validate_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_foreign_key_app_relatedtesttable"
        VALIDATE CONSTRAINT "idempotency_add_colu_test_model_id_99eba75b_fk_idempoten";
    """)
    _create_index_sql = one_line_sql("""
        CREATE INDEX CONCURRENTLY "idempotency_add_column_for_test_model_id_99eba75b"
        ON "idempotency_add_column_foreign_key_app_relatedtesttable" ("test_model_id");
    """)

    _drop_index_sql = one_line_sql("""
        DROP INDEX CONCURRENTLY IF EXISTS "idempotency_add_column_for_test_model_id_99eba75b";
    """)
    _drop_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "idempotency_add_colu_test_model_id_99eba75b_fk_idempoten" IMMEDIATE;
        ALTER TABLE "idempotency_add_column_foreign_key_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_colu_test_model_id_99eba75b_fk_idempoten";
    """)
    _drop_column_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_foreign_key_app_relatedtesttable"
        DROP COLUMN "test_model_id" CASCADE;
    """)

    # get target schema
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    old_schema = pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable")
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    new_schema = pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_column_foreign_key_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _add_column_sql,
        _create_foreign_key_constraint_sql,
        _validate_foreign_key_constraint_sql,
        _create_index_sql,
    ]

    # migrate case 1
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    assert pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable") == new_schema

    # migrate case 2
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    assert pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable") == new_schema

    # migrate case 3
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
        cursor.execute(_validate_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    assert pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable") == new_schema

    # migrate case 4.1
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
        cursor.execute(_validate_foreign_key_constraint_sql)
        cursor.execute(_create_index_sql)
    assert is_valid_index(
        "idempotency_add_column_foreign_key_app_relatedtesttable",
        "idempotency_add_column_for_test_model_id_99eba75b",
    )
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    assert pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_column_foreign_key_app_relatedtesttable",
        "idempotency_add_column_for_test_model_id_99eba75b",
    )

    # migrate case 4.2
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
        cursor.execute(_validate_foreign_key_constraint_sql)
        cursor.execute(_create_index_sql)
    make_index_invalid(
        "idempotency_add_column_foreign_key_app_relatedtesttable",
        "idempotency_add_column_for_test_model_id_99eba75b",
    )
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    assert pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_column_foreign_key_app_relatedtesttable",
        "idempotency_add_column_for_test_model_id_99eba75b",
    )

    # rollback (covers drop column case)
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_column_foreign_key_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_foreign_key_constraint_sql,
        _drop_index_sql,
        _drop_column_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    assert pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable") == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_column_foreign_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
        cursor.execute(_drop_column_sql)
    call_command("migrate", "idempotency_add_column_foreign_key_app", "0001")
    assert pg_dump("idempotency_add_column_foreign_key_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_column_one_to_one_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_column_one_to_one():
    _add_column_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_one_to_one_app_relatedtesttable"
        ADD COLUMN "test_model_id" integer NULL;
    """)
    _create_unique_index_sql = one_line_sql("""
        CREATE UNIQUE INDEX CONCURRENTLY "idempotency_add_column_o_test_model_id_3c5a49fe_uniq"
        ON "idempotency_add_column_one_to_one_app_relatedtesttable" ("test_model_id");
    """)
    _create_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_one_to_one_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_column_o_test_model_id_3c5a49fe_uniq"
        UNIQUE USING INDEX "idempotency_add_column_o_test_model_id_3c5a49fe_uniq";
    """)
    _create_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_one_to_one_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_colu_test_model_id_3c5a49fe_fk_idempoten"
        FOREIGN KEY ("test_model_id")
        REFERENCES "idempotency_add_column_one_to_one_app_testtable" ("id")
        DEFERRABLE INITIALLY DEFERRED NOT VALID;
    """)
    _validate_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_one_to_one_app_relatedtesttable"
        VALIDATE CONSTRAINT "idempotency_add_colu_test_model_id_3c5a49fe_fk_idempoten";
    """)

    _drop_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_one_to_one_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_column_o_test_model_id_3c5a49fe_uniq";
    """)
    _drop_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "idempotency_add_colu_test_model_id_3c5a49fe_fk_idempoten" IMMEDIATE;
        ALTER TABLE "idempotency_add_column_one_to_one_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_colu_test_model_id_3c5a49fe_fk_idempoten";
    """)
    _drop_column_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_column_one_to_one_app_relatedtesttable"
        DROP COLUMN "test_model_id" CASCADE;
    """)

    # get target schema
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    old_schema = pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable")
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    new_schema = pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_column_one_to_one_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _add_column_sql,
        _create_unique_index_sql,
        _create_unique_constraint_sql,
        _create_foreign_key_constraint_sql,
        _validate_foreign_key_constraint_sql,
    ]

    # migrate case 1
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == new_schema

    # migrate case 2.1
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_unique_index_sql)
    assert is_valid_index(
        "idempotency_add_column_one_to_one_app_relatedtesttable",
        "idempotency_add_column_o_test_model_id_3c5a49fe_uniq",
    )
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_column_one_to_one_app_relatedtesttable",
        "idempotency_add_column_o_test_model_id_3c5a49fe_uniq",
    )

    # migrate case 2.2
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_unique_index_sql)
    make_index_invalid(
        "idempotency_add_column_one_to_one_app_relatedtesttable",
        "idempotency_add_column_o_test_model_id_3c5a49fe_uniq",
    )
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_column_one_to_one_app_relatedtesttable",
        "idempotency_add_column_o_test_model_id_3c5a49fe_uniq",
    )

    # migrate case 3
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == new_schema

    # migrate case 4
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == new_schema

    # migrate case 5
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_add_column_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
        cursor.execute(_validate_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == new_schema

    # rollback (covers drop column case)
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_column_one_to_one_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_foreign_key_constraint_sql,
        _drop_unique_constraint_sql,
        _drop_column_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_column_one_to_one_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
        cursor.execute(_drop_column_sql)
    call_command("migrate", "idempotency_add_column_one_to_one_app", "0001")
    assert pg_dump("idempotency_add_column_one_to_one_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_set_not_null_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_set_not_null():
    _create_check_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_set_not_null_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_set_not_nu_test_field_int_76dfbad6_notnull"
        CHECK ("test_field_int" IS NOT NULL) NOT VALID;
    """)
    _validate_check_constraint_sql = one_line_sql(
        """
        ALTER TABLE "idempotency_set_not_null_app_relatedtesttable"
        VALIDATE CONSTRAINT "idempotency_set_not_nu_test_field_int_76dfbad6_notnull";
    """)
    _set_column_not_null_sql = one_line_sql("""
        ALTER TABLE "idempotency_set_not_null_app_relatedtesttable"
        ALTER COLUMN "test_field_int" SET NOT NULL;
    """)
    _drop_check_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_set_not_null_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_set_not_nu_test_field_int_76dfbad6_notnull";
    """)

    _drop_column_not_null_sql = one_line_sql("""
        ALTER TABLE "idempotency_set_not_null_app_relatedtesttable"
        ALTER COLUMN "test_field_int" DROP NOT NULL;
    """)

    # get target schema
    call_command("migrate", "idempotency_set_not_null_app", "0001")
    old_schema = pg_dump("idempotency_set_not_null_app_relatedtesttable")
    call_command("migrate", "idempotency_set_not_null_app")
    new_schema = pg_dump("idempotency_set_not_null_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_set_not_null_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_set_not_null_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_check_constraint_sql,
        _validate_check_constraint_sql,
        _set_column_not_null_sql,
        _drop_check_constraint_sql,
    ]

    # migrate case 1
    call_command("migrate", "idempotency_set_not_null_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_check_constraint_sql)
    call_command("migrate", "idempotency_set_not_null_app")
    assert pg_dump("idempotency_set_not_null_app_relatedtesttable") == new_schema

    # migrate case 2
    call_command("migrate", "idempotency_set_not_null_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_check_constraint_sql)
        cursor.execute(_validate_check_constraint_sql)
    call_command("migrate", "idempotency_set_not_null_app")
    assert pg_dump("idempotency_set_not_null_app_relatedtesttable") == new_schema

    # migrate case 3
    call_command("migrate", "idempotency_set_not_null_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_check_constraint_sql)
        cursor.execute(_validate_check_constraint_sql)
        cursor.execute(_set_column_not_null_sql)
    call_command("migrate", "idempotency_set_not_null_app")
    assert pg_dump("idempotency_set_not_null_app_relatedtesttable") == new_schema

    # migrate case 4
    call_command("migrate", "idempotency_set_not_null_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_check_constraint_sql)
        cursor.execute(_validate_check_constraint_sql)
        cursor.execute(_set_column_not_null_sql)
        cursor.execute(_drop_check_constraint_sql)
    call_command("migrate", "idempotency_set_not_null_app")
    assert pg_dump("idempotency_set_not_null_app_relatedtesttable") == new_schema

    # rollback (covers drop not null case)
    call_command("migrate", "idempotency_set_not_null_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_set_not_null_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_column_not_null_sql
    ]

    # rollback case 1
    call_command("migrate", "idempotency_set_not_null_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_column_not_null_sql)
    call_command("migrate", "idempotency_set_not_null_app", "0001")
    assert pg_dump("idempotency_set_not_null_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_check_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_check():
    _create_check_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_check_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_check_app_relatedtesttable_check"
        CHECK ("test_field_int" > 0) NOT VALID;
    """)
    _validate_check_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_check_app_relatedtesttable"
        VALIDATE CONSTRAINT "idempotency_add_check_app_relatedtesttable_check";
    """)

    _drop_check_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_check_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_check_app_relatedtesttable_check";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_check_app", "0001")
    old_schema = pg_dump("idempotency_add_check_app_relatedtesttable")
    call_command("migrate", "idempotency_add_check_app")
    new_schema = pg_dump("idempotency_add_check_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_check_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_check_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_check_constraint_sql,
        _validate_check_constraint_sql,
    ]

    # migrate case 1
    call_command("migrate", "idempotency_add_check_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_check_constraint_sql)
    call_command("migrate", "idempotency_add_check_app")
    assert pg_dump("idempotency_add_check_app_relatedtesttable") == new_schema

    # migrate case 2
    call_command("migrate", "idempotency_add_check_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_check_constraint_sql)
        cursor.execute(_validate_check_constraint_sql)
    call_command("migrate", "idempotency_add_check_app")
    assert pg_dump("idempotency_add_check_app_relatedtesttable") == new_schema

    # rollback (covers drop check case)
    call_command("migrate", "idempotency_add_check_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_check_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_check_constraint_sql
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_check_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_check_constraint_sql)
    call_command("migrate", "idempotency_add_check_app", "0001")
    assert pg_dump("idempotency_add_check_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_foreign_key_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_foreign_key():
    _create_index_sql = one_line_sql("""
        CREATE INDEX CONCURRENTLY "idempotency_add_foreign_ke_test_field_int_fa01ee40"
        ON "idempotency_add_foreign_key_app_relatedtesttable" ("test_field_int");
    """)
    _create_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_foreign_key_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_fore_test_field_int_fa01ee40_fk_idempoten"
        FOREIGN KEY ("test_field_int")
        REFERENCES "idempotency_add_foreign_key_app_testtable" ("id")
        DEFERRABLE INITIALLY DEFERRED NOT VALID;
    """)
    _validate_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_foreign_key_app_relatedtesttable"
        VALIDATE CONSTRAINT "idempotency_add_fore_test_field_int_fa01ee40_fk_idempoten";
    """)

    _drop_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "idempotency_add_fore_test_field_int_fa01ee40_fk_idempoten" IMMEDIATE;
        ALTER TABLE "idempotency_add_foreign_key_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_fore_test_field_int_fa01ee40_fk_idempoten";
    """)
    _drop_index_sql = one_line_sql("""
        DROP INDEX CONCURRENTLY IF EXISTS "idempotency_add_foreign_ke_test_field_int_fa01ee40";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    old_schema = pg_dump("idempotency_add_foreign_key_app_relatedtesttable")
    call_command("migrate", "idempotency_add_foreign_key_app")
    new_schema = pg_dump("idempotency_add_foreign_key_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_foreign_key_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_index_sql,
        _create_foreign_key_constraint_sql,
        _validate_foreign_key_constraint_sql,
    ]

    # migrate case 1.1
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
    assert is_valid_index(
        "idempotency_add_foreign_key_app_relatedtesttable",
        "idempotency_add_foreign_ke_test_field_int_fa01ee40",
    )
    call_command("migrate", "idempotency_add_foreign_key_app")
    assert pg_dump("idempotency_add_foreign_key_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_foreign_key_app_relatedtesttable",
        "idempotency_add_foreign_ke_test_field_int_fa01ee40",
    )

    # migrate case 1.2
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
    make_index_invalid(
        "idempotency_add_foreign_key_app_relatedtesttable",
        "idempotency_add_foreign_ke_test_field_int_fa01ee40",
    )
    call_command("migrate", "idempotency_add_foreign_key_app")
    assert pg_dump("idempotency_add_foreign_key_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_foreign_key_app_relatedtesttable",
        "idempotency_add_foreign_ke_test_field_int_fa01ee40",
    )

    # migrate case 2
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_foreign_key_app")
    assert pg_dump("idempotency_add_foreign_key_app_relatedtesttable") == new_schema

    # migrate case 3
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
        cursor.execute(_validate_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_foreign_key_app")
    assert pg_dump("idempotency_add_foreign_key_app_relatedtesttable") == new_schema

    # rollback (covers drop foreign key case)
    call_command("migrate", "idempotency_add_foreign_key_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_foreign_key_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_foreign_key_constraint_sql,
        _drop_index_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_foreign_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    assert pg_dump("idempotency_add_foreign_key_app_relatedtesttable") == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_foreign_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
        cursor.execute(_drop_index_sql)
    call_command("migrate", "idempotency_add_foreign_key_app", "0001")
    assert pg_dump("idempotency_add_foreign_key_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_one_to_one_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_one_to_one():
    _create_unique_index_sql = one_line_sql("""
        CREATE UNIQUE INDEX CONCURRENTLY "idempotency_add_one_to_o_test_field_int_8ebac681_uniq"
        ON "idempotency_add_one_to_one_app_relatedtesttable" ("test_field_int");
    """)
    _create_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_one_to_one_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_one_to_o_test_field_int_8ebac681_uniq"
        UNIQUE USING INDEX "idempotency_add_one_to_o_test_field_int_8ebac681_uniq";
    """)
    _create_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_one_to_one_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_one__test_field_int_8ebac681_fk_idempoten"
        FOREIGN KEY ("test_field_int")
        REFERENCES "idempotency_add_one_to_one_app_testtable" ("id")
        DEFERRABLE INITIALLY DEFERRED NOT VALID;
    """)
    _validate_foreign_key_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_one_to_one_app_relatedtesttable"
        VALIDATE CONSTRAINT "idempotency_add_one__test_field_int_8ebac681_fk_idempoten";
    """)

    _drop_foreign_key_constraint_sql = one_line_sql("""
        SET CONSTRAINTS "idempotency_add_one__test_field_int_8ebac681_fk_idempoten" IMMEDIATE;
        ALTER TABLE "idempotency_add_one_to_one_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_one__test_field_int_8ebac681_fk_idempoten";
    """)
    _drop_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_one_to_one_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_one_to_o_test_field_int_8ebac681_uniq";
    """)
    _drop_like_index_sql = one_line_sql("""
        DROP INDEX CONCURRENTLY IF EXISTS "idempotency_add_one_to_o_test_field_int_8ebac681_like";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    old_schema = pg_dump("idempotency_add_one_to_one_app_relatedtesttable")
    call_command("migrate", "idempotency_add_one_to_one_app")
    new_schema = pg_dump("idempotency_add_one_to_one_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_one_to_one_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_unique_index_sql,
        _create_unique_constraint_sql,
        _create_foreign_key_constraint_sql,
        _validate_foreign_key_constraint_sql,
    ]

    # migrate case 1.1
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
    assert is_valid_index(
        "idempotency_add_one_to_one_app_relatedtesttable",
        "idempotency_add_one_to_o_test_field_int_8ebac681_uniq",
    )
    call_command("migrate", "idempotency_add_one_to_one_app")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_one_to_one_app_relatedtesttable",
        "idempotency_add_one_to_o_test_field_int_8ebac681_uniq",
    )

    # migrate case 1.2
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
    make_index_invalid(
        "idempotency_add_one_to_one_app_relatedtesttable",
        "idempotency_add_one_to_o_test_field_int_8ebac681_uniq",
    )
    call_command("migrate", "idempotency_add_one_to_one_app")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_one_to_one_app_relatedtesttable",
        "idempotency_add_one_to_o_test_field_int_8ebac681_uniq",
    )

    # migrate case 2
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
    call_command("migrate", "idempotency_add_one_to_one_app")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == new_schema

    # migrate case 3
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_one_to_one_app")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == new_schema

    # migrate case 4
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
        cursor.execute(_create_foreign_key_constraint_sql)
        cursor.execute(_validate_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_one_to_one_app")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == new_schema

    # rollback (covers drop one to one case)
    call_command("migrate", "idempotency_add_one_to_one_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_one_to_one_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_foreign_key_constraint_sql,
        _drop_unique_constraint_sql,
        _drop_like_index_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_one_to_one_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_one_to_one_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
        cursor.execute(_drop_unique_constraint_sql)
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == old_schema

    # rollback case 3
    call_command("migrate", "idempotency_add_one_to_one_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_foreign_key_constraint_sql)
        cursor.execute(_drop_unique_constraint_sql)
        cursor.execute(_drop_like_index_sql)
    call_command("migrate", "idempotency_add_one_to_one_app", "0001")
    assert pg_dump("idempotency_add_one_to_one_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_index_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_index():
    _create_index_sql = one_line_sql("""
        CREATE INDEX CONCURRENTLY "idempotency_add_index_app__test_field_int_ecc428b5"
        ON "idempotency_add_index_app_relatedtesttable" ("test_field_int");
    """)

    _drop_index_sql = one_line_sql("""
        DROP INDEX CONCURRENTLY IF EXISTS "idempotency_add_index_app__test_field_int_ecc428b5";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_index_app", "0001")
    old_schema = pg_dump("idempotency_add_index_app_relatedtesttable")
    call_command("migrate", "idempotency_add_index_app")
    new_schema = pg_dump("idempotency_add_index_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_index_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_index_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_index_sql,
    ]

    # migrate case 1.1
    call_command("migrate", "idempotency_add_index_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
    assert is_valid_index(
        "idempotency_add_index_app_relatedtesttable",
        "idempotency_add_index_app__test_field_int_ecc428b5",
    )
    call_command("migrate", "idempotency_add_index_app")
    assert pg_dump("idempotency_add_index_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_index_app_relatedtesttable",
        "idempotency_add_index_app__test_field_int_ecc428b5",
    )

    # migrate case 1.2
    call_command("migrate", "idempotency_add_index_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
    make_index_invalid(
        "idempotency_add_index_app_relatedtesttable",
        "idempotency_add_index_app__test_field_int_ecc428b5",
    )
    call_command("migrate", "idempotency_add_index_app")
    assert pg_dump("idempotency_add_index_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_index_app_relatedtesttable",
        "idempotency_add_index_app__test_field_int_ecc428b5",
    )

    # rollback (covers drop index case)
    call_command("migrate", "idempotency_add_index_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_index_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_index_sql
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_index_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_index_sql)
    call_command("migrate", "idempotency_add_index_app", "0001")
    assert pg_dump("idempotency_add_index_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_index_meta_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_index_meta():
    _create_index_sql = one_line_sql("""
        CREATE INDEX CONCURRENTLY "relatedtesttable_idx"
        ON "idempotency_add_index_meta_app_relatedtesttable" ("test_field_int", "test_field_str");
    """)

    _drop_index_sql = one_line_sql("""
        DROP INDEX CONCURRENTLY IF EXISTS "relatedtesttable_idx";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_index_meta_app", "0001")
    old_schema = pg_dump("idempotency_add_index_meta_app_relatedtesttable")
    call_command("migrate", "idempotency_add_index_meta_app")
    new_schema = pg_dump("idempotency_add_index_meta_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_index_meta_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_index_meta_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_index_sql,
    ]

    # migrate case 1.1
    call_command("migrate", "idempotency_add_index_meta_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
    assert is_valid_index(
        "idempotency_add_index_meta_app_relatedtesttable",
        "relatedtesttable_idx",
    )
    call_command("migrate", "idempotency_add_index_meta_app")
    assert pg_dump("idempotency_add_index_meta_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_index_meta_app_relatedtesttable",
        "relatedtesttable_idx",
    )

    # migrate case 1.2
    call_command("migrate", "idempotency_add_index_meta_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_index_sql)
    make_index_invalid(
        "idempotency_add_index_meta_app_relatedtesttable",
        "relatedtesttable_idx",
    )
    call_command("migrate", "idempotency_add_index_meta_app")
    assert pg_dump("idempotency_add_index_meta_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_index_meta_app_relatedtesttable",
        "relatedtesttable_idx",
    )

    # rollback (covers drop index case)
    call_command("migrate", "idempotency_add_index_meta_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_index_meta_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_index_sql
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_index_meta_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_index_sql)
    call_command("migrate", "idempotency_add_index_meta_app", "0001")
    assert pg_dump("idempotency_add_index_meta_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_unique_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_unique():
    _create_unique_index_sql = one_line_sql("""
        CREATE UNIQUE INDEX CONCURRENTLY "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq"
        ON "idempotency_add_unique_app_relatedtesttable" ("test_field_int");
    """)
    _create_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_unique_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq"
        UNIQUE USING INDEX "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq";
    """)

    _drop_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_unique_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq";
    """)
    _drop_like_index_sql = one_line_sql("""
        DROP INDEX CONCURRENTLY IF EXISTS "idempotency_add_unique_a_test_field_int_01c4f0c0_like";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_unique_app", "0001")
    old_schema = pg_dump("idempotency_add_unique_app_relatedtesttable")
    call_command("migrate", "idempotency_add_unique_app")
    new_schema = pg_dump("idempotency_add_unique_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_unique_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_unique_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_unique_index_sql,
        _create_unique_constraint_sql,
    ]

    # migrate case 1.1
    call_command("migrate", "idempotency_add_unique_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
    assert is_valid_index(
        "idempotency_add_unique_app_relatedtesttable",
        "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq",
    )
    call_command("migrate", "idempotency_add_unique_app")
    assert pg_dump("idempotency_add_unique_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_unique_app_relatedtesttable",
        "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq",
    )

    # migrate case 1.2
    call_command("migrate", "idempotency_add_unique_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
    make_index_invalid(
        "idempotency_add_unique_app_relatedtesttable",
        "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq",
    )
    call_command("migrate", "idempotency_add_unique_app")
    assert pg_dump("idempotency_add_unique_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_unique_app_relatedtesttable",
        "idempotency_add_unique_a_test_field_int_01c4f0c0_uniq",
    )

    # migrate case 2
    call_command("migrate", "idempotency_add_unique_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
    call_command("migrate", "idempotency_add_unique_app")
    assert pg_dump("idempotency_add_unique_app_relatedtesttable") == new_schema

    # rollback (covers drop unique case)
    call_command("migrate", "idempotency_add_unique_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_unique_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_unique_constraint_sql,
        _drop_like_index_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_unique_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_unique_constraint_sql)
    call_command("migrate", "idempotency_add_unique_app", "0001")
    assert pg_dump("idempotency_add_unique_app_relatedtesttable") == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_unique_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_unique_constraint_sql)
        cursor.execute(_drop_like_index_sql)
    call_command("migrate", "idempotency_add_unique_app", "0001")
    assert pg_dump("idempotency_add_unique_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_unique_meta_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_unique_meta():
    _create_unique_index_sql = one_line_sql("""
        CREATE UNIQUE INDEX CONCURRENTLY "relatedtesttable_uniq"
        ON "idempotency_add_unique_meta_app_relatedtesttable" ("test_field_int", "test_field_str");
    """)
    _create_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_unique_meta_app_relatedtesttable"
        ADD CONSTRAINT "relatedtesttable_uniq"
        UNIQUE USING INDEX "relatedtesttable_uniq";
    """)

    _drop_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_unique_meta_app_relatedtesttable"
        DROP CONSTRAINT "relatedtesttable_uniq";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_unique_meta_app", "0001")
    old_schema = pg_dump("idempotency_add_unique_meta_app_relatedtesttable")
    call_command("migrate", "idempotency_add_unique_meta_app")
    new_schema = pg_dump("idempotency_add_unique_meta_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_unique_meta_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_unique_meta_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _create_unique_index_sql,
        _create_unique_constraint_sql,
    ]

    # migrate case 1.1
    call_command("migrate", "idempotency_add_unique_meta_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
    assert is_valid_index(
        "idempotency_add_unique_meta_app_relatedtesttable",
        "relatedtesttable_uniq",
    )
    call_command("migrate", "idempotency_add_unique_meta_app")
    assert pg_dump("idempotency_add_unique_meta_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_unique_meta_app_relatedtesttable",
        "relatedtesttable_uniq",
    )

    # migrate case 1.2
    call_command("migrate", "idempotency_add_unique_meta_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
    make_index_invalid(
        "idempotency_add_unique_meta_app_relatedtesttable",
        "relatedtesttable_uniq",
    )
    call_command("migrate", "idempotency_add_unique_meta_app")
    assert pg_dump("idempotency_add_unique_meta_app_relatedtesttable") == new_schema
    assert is_valid_index(
        "idempotency_add_unique_meta_app_relatedtesttable",
        "relatedtesttable_uniq",
    )

    # migrate case 2
    call_command("migrate", "idempotency_add_unique_meta_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_unique_constraint_sql)
    call_command("migrate", "idempotency_add_unique_meta_app")
    assert pg_dump("idempotency_add_unique_meta_app_relatedtesttable") == new_schema

    # rollback (covers drop unique case)
    call_command("migrate", "idempotency_add_unique_meta_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_unique_meta_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_unique_constraint_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_unique_meta_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_unique_constraint_sql)
    call_command("migrate", "idempotency_add_unique_meta_app", "0001")
    assert pg_dump("idempotency_add_unique_meta_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_primary_key_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_primary_key():
    _drop_column_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_primary_key_app_relatedtesttable"
        DROP COLUMN "id" CASCADE;
    """)
    _create_unique_index_sql = one_line_sql("""
        CREATE UNIQUE INDEX CONCURRENTLY "idempotency_add_primary_k_test_field_int_e9cebf24_pk"
        ON "idempotency_add_primary_key_app_relatedtesttable" ("test_field_int");
    """)
    _create_primary_key_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_primary_key_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_primary_k_test_field_int_e9cebf24_pk"
        PRIMARY KEY USING INDEX "idempotency_add_primary_k_test_field_int_e9cebf24_pk";
    """)

    _drop_unique_constraint_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_primary_key_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_primary__test_field_int_e9cebf24_uniq";
    """)
    _drop_primary_key_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_primary_key_app_relatedtesttable"
        DROP CONSTRAINT "idempotency_add_primary_k_test_field_int_e9cebf24_pk";
    """)
    _drop_unique_index_sql = one_line_sql("""
        DROP INDEX CONCURRENTLY IF EXISTS "idempotency_add_primary__test_field_int_e9cebf24_like";
    """)
    _add_column_for_rollback_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_primary_key_app_relatedtesttable"
        ADD COLUMN "id" integer NOT NULL GENERATED BY DEFAULT AS IDENTITY;
    """)
    if django.VERSION[:2] < (4, 1):
        _add_column_for_rollback_sql = one_line_sql("""
            ALTER TABLE "idempotency_add_primary_key_app_relatedtesttable"
            ADD COLUMN "id" serial NOT NULL;
        """)
    _create_unique_index_for_rollback_sql = one_line_sql("""
        CREATE UNIQUE INDEX CONCURRENTLY "idempotency_add_primary_key_app_relatedtesttable_id_d0e5667c_pk"
        ON "idempotency_add_primary_key_app_relatedtesttable" ("id");
    """)
    _create_unique_constraint_for_rollback_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_primary_key_app_relatedtesttable"
        ADD CONSTRAINT "idempotency_add_primary_key_app_relatedtesttable_id_d0e5667c_pk"
        PRIMARY KEY USING INDEX "idempotency_add_primary_key_app_relatedtesttable_id_d0e5667c_pk";
    """)

    # get target schema
    call_command("migrate", "idempotency_add_primary_key_app", "0001")
    old_schema = pg_dump("idempotency_add_primary_key_app_relatedtesttable")
    call_command("migrate", "idempotency_add_primary_key_app")
    new_schema = pg_dump("idempotency_add_primary_key_app_relatedtesttable")

    # migrate
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_primary_key_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _drop_column_sql,
        _create_unique_index_sql,
        _create_primary_key_sql,
    ]

    # migrate case 1
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_drop_column_sql)
    call_command("migrate", "idempotency_add_primary_key_app")
    assert pg_dump("idempotency_add_primary_key_app_relatedtesttable") == new_schema

    # migrate case 2.1
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_drop_column_sql)
        cursor.execute(_create_unique_index_sql)
    assert is_valid_index(
        "idempotency_add_primary_key_app_relatedtesttable",
        "idempotency_add_primary_k_test_field_int_e9cebf24_pk",
    )
    call_command("migrate", "idempotency_add_primary_key_app")
    assert pg_dump("idempotency_add_primary_key_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_primary_key_app_relatedtesttable",
        "idempotency_add_primary_k_test_field_int_e9cebf24_pk",
    )

    # migrate case 2.2
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_drop_column_sql)
        cursor.execute(_create_unique_index_sql)
    make_index_invalid(
        "idempotency_add_primary_key_app_relatedtesttable",
        "idempotency_add_primary_k_test_field_int_e9cebf24_pk",
    )
    call_command("migrate", "idempotency_add_primary_key_app")
    assert pg_dump("idempotency_add_primary_key_app_relatedtesttable") == new_schema
    assert is_valid_constraint(
        "idempotency_add_primary_key_app_relatedtesttable",
        "idempotency_add_primary_k_test_field_int_e9cebf24_pk",
    )

    # migrate case 3
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_drop_column_sql)
        cursor.execute(_create_unique_index_sql)
        cursor.execute(_create_primary_key_sql)
    call_command("migrate", "idempotency_add_primary_key_app")
    assert pg_dump("idempotency_add_primary_key_app_relatedtesttable") == new_schema

    # rollback (covers drop primary key case)
    call_command("migrate", "idempotency_add_primary_key_app")
    with override_settings(
        ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False,
        ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False,
    ):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_primary_key_app", "0002")
    if django.VERSION[:2] < (4, 1):
        assert split_sql_queries(rollback_sql) == [
            _drop_unique_constraint_sql,
            _drop_primary_key_sql,
            _drop_unique_index_sql,
            _add_column_for_rollback_sql,
            _create_unique_index_for_rollback_sql,
            _create_unique_constraint_for_rollback_sql,
        ]
    else:
        assert split_sql_queries(rollback_sql) == [
            _drop_primary_key_sql,
            _drop_unique_index_sql,
            _add_column_for_rollback_sql,
            _create_unique_index_for_rollback_sql,
            _create_unique_constraint_for_rollback_sql,
        ]

    def old_schema_compatible(dump: str) -> str:
        """
        django creates different name for primary key constraint than postgres
        rolling back drop index can be reason of columns order changes
        """
        return dump.replace(
            "idempotency_add_primary_key_app_relatedtesttable_id_d0e5667c_pk",
            "idempotency_add_primary_key_app_relatedtesttable_pkey",
        ).replace(
            "test_field_int integer NOT NULL,\n    id integer NOT NULL",
            "id integer NOT NULL,\n    test_field_int integer NOT NULL",
        )

    # rollback case 1
    call_command("migrate", "idempotency_add_primary_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_primary_key_sql)
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    assert old_schema_compatible(pg_dump("idempotency_add_primary_key_app_relatedtesttable")) == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_primary_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_primary_key_sql)
        cursor.execute(_drop_unique_index_sql)
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    assert old_schema_compatible(pg_dump("idempotency_add_primary_key_app_relatedtesttable")) == old_schema

    # rollback case 3
    call_command("migrate", "idempotency_add_primary_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_primary_key_sql)
        cursor.execute(_drop_unique_index_sql)
        cursor.execute(_add_column_for_rollback_sql)
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    assert old_schema_compatible(pg_dump("idempotency_add_primary_key_app_relatedtesttable")) == old_schema

    # rollback case 4
    call_command("migrate", "idempotency_add_primary_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_primary_key_sql)
        cursor.execute(_drop_unique_index_sql)
        cursor.execute(_add_column_for_rollback_sql)
        cursor.execute(_create_unique_index_for_rollback_sql)
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    assert old_schema_compatible(pg_dump("idempotency_add_primary_key_app_relatedtesttable")) == old_schema

    # rollback case 5
    call_command("migrate", "idempotency_add_primary_key_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_primary_key_sql)
        cursor.execute(_drop_unique_index_sql)
        cursor.execute(_add_column_for_rollback_sql)
        cursor.execute(_create_unique_index_for_rollback_sql)
        cursor.execute(_create_unique_constraint_for_rollback_sql)
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_primary_key_app", "0001")
    assert old_schema_compatible(pg_dump("idempotency_add_primary_key_app_relatedtesttable")) == old_schema


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_auto_field_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_auto_field():
    _set_type_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_auto_field_app_relatedtesttable"
        ALTER COLUMN "test_field_int" TYPE integer;
    """)
    _set_identity_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_auto_field_app_relatedtesttable"
        ALTER COLUMN "test_field_int" ADD GENERATED BY DEFAULT AS IDENTITY;
    """)

    _drop_identity_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_auto_field_app_relatedtesttable"
        ALTER COLUMN "test_field_int" DROP IDENTITY IF EXISTS;
    """)
    _set_type_for_rollback_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_auto_field_app_relatedtesttable"
        ALTER COLUMN "test_field_int" TYPE integer;
    """)
    _sql_drop_sequence_sql = one_line_sql("""
        DROP SEQUENCE IF EXISTS "idempotency_add_auto_field_app_relatedtestta_test_field_int_seq" CASCADE;
    """)

    # get target schema
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    old_schema = pg_dump("idempotency_add_auto_field_app_relatedtesttable")
    call_command("migrate", "idempotency_add_auto_field_app")
    new_schema = pg_dump("idempotency_add_auto_field_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_auto_field_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _set_type_sql,
        _set_identity_sql,
    ]

    # migrate case 1
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == new_schema

    # migrate case 2
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
        cursor.execute(_set_identity_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == new_schema

    # rollback (covers drop auto field case)
    call_command("migrate", "idempotency_add_auto_field_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_auto_field_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _drop_identity_sql,
        _set_type_for_rollback_sql,
        _sql_drop_sequence_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_auto_field_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_identity_sql)
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_auto_field_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_identity_sql)
        cursor.execute(_set_type_for_rollback_sql)
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == old_schema

    # rollback case 3
    call_command("migrate", "idempotency_add_auto_field_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_identity_sql)
        cursor.execute(_set_type_for_rollback_sql)
        cursor.execute(_sql_drop_sequence_sql)
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == old_schema


@skip_for_default_django_backend
@pytest.mark.skipif(
    django.VERSION[:2] >= (4, 1),
    reason="django before 4.1 case",
)
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={"append": "tests.apps.idempotency_add_auto_field_app"})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
@override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=True)
def test_idempotency_add_auto_field_old():
    _set_type_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_auto_field_app_relatedtesttable"
        ALTER COLUMN "test_field_int" TYPE integer USING "test_field_int"::integer;
    """)
    _drop_sequence_sql = one_line_sql("""
        DROP SEQUENCE IF EXISTS "idempotency_add_auto_field_app_relatedtesttable_test_field_int_seq" CASCADE;
    """)
    _create_sequence_sql = one_line_sql("""
        CREATE SEQUENCE "idempotency_add_auto_field_app_relatedtesttable_test_field_int_seq";
    """)
    _set_default_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_auto_field_app_relatedtesttable"
        ALTER COLUMN "test_field_int"
        SET DEFAULT nextval(\'"idempotency_add_auto_field_app_relatedtesttable_test_field_int_seq"\');
    """)
    _set_max_value_sql = one_line_sql("""
        SELECT setval('"idempotency_add_auto_field_app_relatedtesttable_test_field_int_seq"', MAX("test_field_int"))
        FROM "idempotency_add_auto_field_app_relatedtesttable";
    """)
    _set_owner_sql = one_line_sql("""
        ALTER SEQUENCE "idempotency_add_auto_field_app_relatedtesttable_test_field_int_seq"
        OWNED BY "idempotency_add_auto_field_app_relatedtesttable"."test_field_int";
    """)

    _set_type_for_rollback_sql = one_line_sql("""
        ALTER TABLE "idempotency_add_auto_field_app_relatedtesttable"
        ALTER COLUMN "test_field_int" TYPE integer USING "test_field_int"::integer;
    """)
    _drop_sequence_sql = one_line_sql("""
        DROP SEQUENCE IF EXISTS "idempotency_add_auto_field_app_relatedtesttable_test_field_int_seq" CASCADE;
    """)

    # get target schema
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    old_schema = pg_dump("idempotency_add_auto_field_app_relatedtesttable")
    call_command("migrate", "idempotency_add_auto_field_app")
    new_schema = pg_dump("idempotency_add_auto_field_app_relatedtesttable")

    # migrate
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        migration_sql = call_command("sqlmigrate", "idempotency_add_auto_field_app", "0002")
    assert split_sql_queries(migration_sql) == [
        _set_type_sql,
        _drop_sequence_sql,
        _create_sequence_sql,
        _set_default_sql,
        _set_max_value_sql,
        _set_owner_sql,
    ]

    def schema_compatible_sequence_alter(dump: str) -> str:
        return dump.replace(
            textwrap.dedent("""
                CREATE TABLE public.idempotency_add_auto_field_app_relatedtesttable (
                    test_field_int integer DEFAULT
                    nextval('public.idempotency_add_auto_field_app_relatedtesttable_test_field_int_'::regclass) NOT NULL
                );


                ALTER TABLE public.idempotency_add_auto_field_app_relatedtesttable OWNER TO test;
            """).replace("\n    nextval", " nextval"),
            textwrap.dedent("""
                CREATE TABLE public.idempotency_add_auto_field_app_relatedtesttable (
                    test_field_int integer NOT NULL
                );


                ALTER TABLE public.idempotency_add_auto_field_app_relatedtesttable OWNER TO test;

                --
                -- Name: idempotency_add_auto_field_app_relatedtesttable_test_field_int_;
                -- Type: SEQUENCE; Schema: public; Owner: test
                --

                CREATE SEQUENCE public.idempotency_add_auto_field_app_relatedtesttable_test_field_int_
                    START WITH 1
                    INCREMENT BY 1
                    NO MINVALUE
                    NO MAXVALUE
                    CACHE 1;


                ALTER SEQUENCE public.idempotency_add_auto_field_app_relatedtesttable_test_field_int_ OWNER TO test;

                --
                -- Name: idempotency_add_auto_field_app_relatedtesttable_test_field_int_;
                -- Type: SEQUENCE OWNED BY; Schema: public; Owner: test
                --

                ALTER SEQUENCE public.idempotency_add_auto_field_app_relatedtesttable_test_field_int_
                OWNED BY public.idempotency_add_auto_field_app_relatedtesttable.test_field_int;


                --
                -- Name: idempotency_add_auto_field_app_relatedtesttable test_field_int;
                -- Type: DEFAULT; Schema: public; Owner: test
                --

                ALTER TABLE ONLY public.idempotency_add_auto_field_app_relatedtesttable ALTER COLUMN test_field_int
                SET DEFAULT nextval('public.idempotency_add_auto_field_app_relatedtesttable_test_field_int_'::regclass);

            """).replace("\n-- Type", " Type").replace("\nOWNED", " OWNED").replace("\nSET", " SET"),
        )

    def schema_compatible_explicit_type(dump: str) -> str:
        return dump.replace(
            textwrap.dedent("""
                CREATE SEQUENCE public.idempotency_add_auto_field_app_relatedtesttable_test_field_int_
                    AS integer
                    START WITH 1
                    INCREMENT BY 1
                    NO MINVALUE
                    NO MAXVALUE
                    CACHE 1;
            """),
            textwrap.dedent("""
                CREATE SEQUENCE public.idempotency_add_auto_field_app_relatedtesttable_test_field_int_
                    START WITH 1
                    INCREMENT BY 1
                    NO MINVALUE
                    NO MAXVALUE
                    CACHE 1;
            """),
        )

    # migrate case 1
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == new_schema

    # migrate case 2
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
        cursor.execute(_drop_sequence_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == new_schema

    # migrate case 3
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
        cursor.execute(_drop_sequence_sql)
        cursor.execute(_create_sequence_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == new_schema

    # migrate case 4
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
        cursor.execute(_drop_sequence_sql)
        cursor.execute(_create_sequence_sql)
        cursor.execute(_set_default_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert schema_compatible_sequence_alter(
        pg_dump("idempotency_add_auto_field_app_relatedtesttable")
    ) == new_schema

    # migrate case 5
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
        cursor.execute(_drop_sequence_sql)
        cursor.execute(_create_sequence_sql)
        cursor.execute(_set_default_sql)
        cursor.execute(_set_max_value_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert schema_compatible_sequence_alter(
        pg_dump("idempotency_add_auto_field_app_relatedtesttable")
    ) == new_schema

    # migrate case 6
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False):
        call_command("migrate", "idempotency_add_auto_field_app", "0001")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_sql)
        cursor.execute(_drop_sequence_sql)
        cursor.execute(_create_sequence_sql)
        cursor.execute(_set_default_sql)
        cursor.execute(_set_max_value_sql)
        cursor.execute(_set_owner_sql)
    call_command("migrate", "idempotency_add_auto_field_app")
    assert schema_compatible_explicit_type(pg_dump("idempotency_add_auto_field_app_relatedtesttable")) == new_schema

    # rollback (covers drop auto field case)
    call_command("migrate", "idempotency_add_auto_field_app")
    with override_settings(ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL=False):
        rollback_sql = call_command("sqlmigrate", "--backwards", "idempotency_add_auto_field_app", "0002")
    assert split_sql_queries(rollback_sql) == [
        _set_type_for_rollback_sql,
        _drop_sequence_sql,
    ]

    # rollback case 1
    call_command("migrate", "idempotency_add_auto_field_app")
    with connection.cursor() as cursor:
        cursor.execute(_set_type_for_rollback_sql)
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == old_schema

    # rollback case 2
    call_command("migrate", "idempotency_add_auto_field_app")
    with connection.cursor() as cursor:
        cursor.execute(_drop_sequence_sql)
    call_command("migrate", "idempotency_add_auto_field_app", "0001")
    assert pg_dump("idempotency_add_auto_field_app_relatedtesttable") == old_schema
