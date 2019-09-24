from django.conf import settings

import pytest

skip_for_default_django_backend = pytest.mark.skipif(
    settings.DATABASES['default']['ENGINE'] in (
        'django.db.backends.postgresql',
        'django.contrib.gis.db.backends.postgis',
    ),
    reason='not actual for default django backends'
)
