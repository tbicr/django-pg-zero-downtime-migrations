from .settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django_zero_downtime_migrations_postgres_backend',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'postgres',
        'PORT': '5432',
    },
}
