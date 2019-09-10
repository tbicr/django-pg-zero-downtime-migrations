# django-pg-zero-downtime-migrations changelog

## 0.6
  - marked `AddField` with `null=False` parameter and compatible `CHECK IS NOT NULL` constraint option as unsafe operation
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
