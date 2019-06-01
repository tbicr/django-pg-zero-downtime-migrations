import warnings

warnings.warn(
    '`django_zero_downtime_migrations_postgres_backend` module is deprecated and can be removed in future versions,'
    ' please use `django_zero_downtime_migrations.backends.postgres` instead.',
    DeprecationWarning,
)
