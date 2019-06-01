# django-pg-zero-downtime-migrations changelog

## 0.5
  - extract zero-downtime-schema to mixin to allow use this logic with other backends
  - move module from `django_zero_downtime_migrations_postgres_backend` to `django_zero_downtime_migrations.backends.postgres`
  - mark `django_zero_downtime_migrations_postgres_backend` module as deprecated

## 0.4
  - change defaults for `ZERO_DOWNTIME_MIGRATIONS_LOCK_TIMEOUT` and `ZERO_DOWNTIME_MIGRATIONS_STATEMENT_TIMEOUT` from `0ms` to `None` to get same with default django behavior that respect default postgres timeouts
  - add updates to documentations with options defaults
  - add updates to documentations with best options usage
  - fix adding nullable field with default had no error and warning issue
  - add links to documentation with issue describing and safe alternatives usage for errors and warnings
  - add updates to documentations with type casting workarounds
  
## 0.3
  - add django 2.2 support with `Meta.indexes` and `Meta.constraints` attributes
  - fix python deprecation warnings for regexp
  - remove unused `TimeoutException`
  - improve README and PYPI description

## 0.2
  - add option that allow disable `statement_timeout` for long operations like index creation on constraint validation when statement_timeout set globally

## 0.1.1
  - add long description content type

## 0.1
  - first release:
    - replace default sql queries with more safe
    - add options for `statement_timeout` and `lock_timeout`
    - add option for `NOT NULL` constraint behaviour
    - add option for unsafe operation restriction
