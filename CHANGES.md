# django-pg-zero-downtime-migrations Changelog

## 0.18
- split CI into smaller jobs

## 0.17
- added django 5.1 support
- added python 3.13 support
- added postgres 17 support
- marked postgres 12 support as deprecated
- marked postgres 13 support as deprecated
- dropped django 3.2 support
- dropped django 4.0 support
- dropped django 4.1 support
- dropped python 3.6 support
- dropped python 3.7 support
- dropped `migrate_isnotnull_check_constraints` command

## 0.16
- changed `ADD COLUMN DEFAULT NULL` to a safe operation for code defaults
- changed `ADD COLUMN DEFAULT NOT NULL` to a safe operation for `db_default` in django 5.0+
- added the `ZERO_DOWNTIME_MIGRATIONS_KEEP_DEFAULT` setting and changed `ADD COLUMN DEFAULT NOT NULL` with this setting to a safe operation for django < 5.0
- added the `ZERO_DOWNTIME_MIGRATIONS_EXPLICIT_CONSTRAINTS_DROP` setting and enabled dropping constraints and indexes before dropping a column or table
- fixed `sqlmigrate` in idempotent mode
- fixed unique constraint creation with the `include` parameter
- fixed idempotent mode tests
- updated unsafe migration links to the documentation
- updated patched code to the latest django version
- updated test image to ubuntu 24.04
- improved README

## 0.15
- added idempotent mode and the `ZERO_DOWNTIME_MIGRATIONS_IDEMPOTENT_SQL` setting
- fixed django 3.2 degradation due to the missing `skip_default_on_alter` method
- improved README
- updated the release github action

## 0.14
- fixed deferred sql errors
- added django 5.0 support
- added python 3.12 support
- added postgres 16 support
- dropped postgres 11 support
- removed the `ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL` setting
- marked the `migrate_isnotnull_check_constraints` command as deprecated

## 0.13
- added django 4.2 support
- marked django 3.2 support as deprecated
- marked django 4.0 support as deprecated
- marked django 4.1 support as deprecated
- marked postgres 11 support as deprecated
- dropped postgres 10 support
- updated the test docker image to ubuntu 22.04

## 0.12
- added support for `serial` and `integer`, `bigserial` and `bigint`, as well as `smallserial` and `smallint`, implementing the same type changes as safe migrations
- fixed the `AutoField` type change and concurrent insertion issue for django < 4.1
- added sequence dropping and creation timeouts, as they can be used with the `CASCADE` keyword and may affect other tables
- added django 4.1 support
- added python 3.11 support
- added postgres 15 support
- marked postgres 10 support as deprecated
- dropped django 2.2 support
- dropped django 3.0 support
- dropped django 3.1 support
- dropped postgres 9.5 support
- dropped postgres 9.6 support
- added github actions checks for pull requests

## 0.11
- fixed an issue where renaming a model while keeping `db_table` raised an `ALTER_TABLE_RENAME` error (#26)
- added django 3.2 support
- added django 4.0 support
- added python 3.9 support
- added python 3.10 support
- added postgres 14 support
- marked django 2.2 support as deprecated
- marked django 3.0 support as deprecated
- marked django 3.1 support as deprecated
- marked python 3.6 support as deprecated
- marked python 3.7 support as deprecated
- marked postgres 9.5 support as deprecated
- marked postgres 9.6 support as deprecated
- switched to github actions for testing

## 0.10
- added django 3.1 support
- added postgres 13 support
- dropped python 3.5 support
- updated the test environment

## 0.9
- fixed the decimal-to-float migration error
- fixed tests for django 3.0.2 and later

## 0.8
- added django 3.0 support
- added support for concurrent index creation and removal operations
- added support for exclude constraints as an unsafe operation
- dropped postgres 9.4 support
- dropped django 2.0 support
- dropped django 2.1 support
- removed the deprecated `django_zero_downtime_migrations_postgres_backend` module

## 0.7
- added python 3.8 support
- added support for postgres-specific indexes
- improved test clarity
- fixed regexp escaping warnings in the management command
- fixed style checks
- improved README
- marked python 3.5 support as deprecated
- marked postgres 9.4 support as deprecated
- marked django 2.0 support as deprecated
- marked django 2.1 support as deprecated

## 0.6
- marked the `ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL` option as deprecated for postgres 12+
- added a management command for migrating from a `CHECK IS NOT NULL` constraint to a real `NOT NULL` constraint
- added integration tests for postgres 12, postgres 11 (root), postgres 11 with compatible not null constraints, postgres 11 with standard not null constraints, as well as postgres 10, 9.6, 9.5, 9.4, and postgis databases
- fixed bugs related to the deletion and creation of compatible check not null constraints via `pg_attribute`
- minimized side effects with deferred sql execution between operations in one migration module
- added safe `NOT NULL` constraint creation for postgres 12
- added safe `NOT NULL` constraint creation for extra permissions for `pg_catalog.pg_attribute` when the `ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=USE_PG_ATTRIBUTE_UPDATE_FOR_SUPERUSER` option is enabled
- marked `AddField` with the `null=False` parameter and the compatible `CHECK IS NOT NULL` constraint option as an unsafe operation, ignoring the `ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL` value in this case
- added versioning to the package
- fixed pypi README image links
- improved README

## 0.5
- extracted zero-downtime-schema logic into a mixin to allow using it with other backends
- moved the module from `django_zero_downtime_migrations_postgres_backend` to `django_zero_downtime_migrations.backends.postgres`
- marked the `django_zero_downtime_migrations_postgres_backend` module as deprecated
- added support for the postgis backend
- improved README

## 0.4
- changed the defaults for `ZERO_DOWNTIME_MIGRATIONS_LOCK_TIMEOUT` and `ZERO_DOWNTIME_MIGRATIONS_STATEMENT_TIMEOUT` from `0ms` to `None` to match the default django behavior that respects postgres timeouts
- updated the documentation with option defaults
- updated the documentation with best practices for option usage
- fixed the issue where adding a nullable field with a default did not raise an error or warning
- added links to the documentation describing the issue and safe alternative usage for errors and warnings
- updated the documentation with type casting workarounds

## 0.3
- added django 2.2 support with the `Meta.indexes` and `Meta.constraints` attributes
- fixed python deprecation warnings for regular expressions
- removed the unused `TimeoutException`
- improved README and PYPI description

## 0.2
- added an option to disable `statement_timeout` for long operations, such as index creation and constraint validation, when `statement_timeout` is set globally

## 0.1.1
- added long description content type

## 0.1
- replaced default sql queries with safer alternatives
- added options for `statement_timeout` and `lock_timeout`
- added an option for `NOT NULL` constraint behavior
- added an option for restricting unsafe operations
