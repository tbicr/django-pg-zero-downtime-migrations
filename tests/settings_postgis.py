from .settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django_zero_downtime_migrations.backends.postgis',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'postgres',
        'PORT': '5432',
    },
}
