# django-pg-zero-downtime-migrations changelog

## 0.12
  - added `serial` and `integer`, `bigserial` and `bigint`, `smallserial` and `smallint`, same types changes as safe migrations
  - fixed `AutoField` type changing and concurrent insertions issue for `django<4.1`
  - added sequence dropping and creation timeouts as they can be used with `CASCADE` keyword and affect other tables
  - added django 4.1 support
  - added python 3.11 support
  - added postgres 15 support
  - marked postgres 10 support deprecated
  - drop django 2.2 support
  - drop django 3.0 support
  - drop django 3.1 support
  - drop postgres 9.5 support
  - drop postgres 9.6 support
  - add github actions checks for pull requests

## 0.11
  - fixed rename model with keeping `db_table` raises `ALTER_TABLE_RENAME` error #26
  - added django 3.2 support
  - added django 4.0 support
  - added python 3.9 support
  - added python 3.10 support
  - added postgres 14 support
  - marked django 2.2 support deprecated
  - marked django 3.0 support deprecated
  - marked django 3.1 support deprecated
  - marked python 3.6 support deprecated
  - marked python 3.7 support deprecated
  - marked postgres 9.5 support deprecated
  - marked postgres 9.6 support deprecated
  - move to github actions for testing

## 0.10
  - added django 3.1 support
  - added postgres 13 support
  - drop python 3.5 support
  - updated test environment

## 0.9
  - fixed decimal to float migration error
  - fixed django 3.0.2+ tests

## 0.8
  - added django 3.0 support
  - added concurrently index creation and removal operations
  - added exclude constraint support as unsafe operation
  - drop postgres 9.4 support
  - drop django 2.0 support
  - drop django 2.1 support
  - drop deprecated `django_zero_downtime_migrations_postgres_backend` module

## 0.7
  - added python 3.8 support
  - added postgres specific indexes support
  - improved tests clearness
  - fixed regexp escaping warning for management command
  - fixed style check
  - improved README
  - marked python 3.5 support deprecated
  - marked postgres 9.4 support deprecated
  - marked django 2.0 support deprecated
  - marked django 2.1 support deprecated

## 0.6
  - marked `ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL` option deprecated for postgres 12+
  - added management command for migration to real `NOT NULL` from `CHECK IS NOT NULL` constraint
  - added integration tests for pg 12, pg 11 root, pg 11 compatible not null constraint, pg 11 standard not null constraint and pg 10, 9.6, 9.5, 9.4, postgis databases
  - fixed compatible check not null constraint deletion and creation via pg_attribute bugs
  - minimized side affect with deferred sql execution between operations in one migration module
  - added postgres 12 safe `NOT NULL` constraint creation
  - added safe `NOT NULL` constraint creation for extra permissions for `pg_catalog.pg_attribute` with `ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL=USE_PG_ATTRIBUTE_UPDATE_FOR_SUPERUSER` option enabled
  - marked `AddField` with `null=False` parameter and compatible `CHECK IS NOT NULL` constraint option as unsafe operation and avoid `ZERO_DOWNTIME_MIGRATIONS_USE_NOT_NULL` value in this case
  - added version to package
  - fixed pypi README images links
  - improved README

## 0.5
  - extracted zero-downtime-schema to mixin to allow use this logic with other backends
  - moved module from `django_zero_downtime_migrations_postgres_backend` to `django_zero_downtime_migrations.backends.postgres`
  - marked `django_zero_downtime_migrations_postgres_backend` module as deprecated
  - added postgis backend support
  - improved README

## 0.4
  - changed defaults for `ZERO_DOWNTIME_MIGRATIONS_LOCK_TIMEOUT` and `ZERO_DOWNTIME_MIGRATIONS_STATEMENT_TIMEOUT` from `0ms` to `None` to get same with default django behavior that respect default postgres timeouts
  - added updates to documentations with options defaults
  - added updates to documentations with best options usage
  - fixed adding nullable field with default had no error and warning issue
  - added links to documentation with issue describing and safe alternatives usage for errors and warnings
  - added updates to documentations with type casting workarounds
  
## 0.3
  - added django 2.2 support with `Meta.indexes` and `Meta.constraints` attributes
  - fixed python deprecation warnings for regexp
  - removed unused `TimeoutException`
  - improved README and PYPI description

## 0.2
  - added option that allow disable `statement_timeout` for long operations like index creation on constraint validation when statement_timeout set globally

## 0.1.1
  - added long description content type

## 0.1
  - replaced default sql queries with more safe
  - added options for `statement_timeout` and `lock_timeout`
  - added option for `NOT NULL` constraint behaviour
  - added option for unsafe operation restriction
