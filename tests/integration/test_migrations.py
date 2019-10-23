from django.conf import settings
from django.test import modify_settings, override_settings

import pytest

from django_zero_downtime_migrations.backends.postgres.schema import (
    UnsafeOperationException
)
from tests import skip_for_default_django_backend
from tests.integration import migrate


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.good_flow_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow():
    # forward
    if settings.DATABASES['default']['HOST'] in ['pg94']:
        migrate(['good_flow_app', '0025'])
    else:
        migrate(['good_flow_app'])

    # backward
    migrate(['good_flow_app', 'zero'])


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.bad_rollback_flow_drop_column_with_notnull_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_rollback_flow_drop_column_with_notnull():
    # forward
    migrate(['bad_rollback_flow_drop_column_with_notnull_app'])

    # backward
    with pytest.raises(UnsafeOperationException):
        migrate(['bad_rollback_flow_drop_column_with_notnull_app', '0001'])


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.bad_rollback_flow_drop_column_with_notnull_default_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_rollback_flow_drop_column_with_notnull_default():
    # forward
    migrate(['bad_rollback_flow_drop_column_with_notnull_default_app'])

    # backward
    with pytest.raises(UnsafeOperationException):
        migrate(['bad_rollback_flow_drop_column_with_notnull_default_app', '0001'])


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.bad_rollback_flow_change_char_type_that_safe_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_rollback_flow_change_char_type_that_safe():
    # forward
    migrate(['bad_rollback_flow_change_char_type_that_safe_app'])

    # backward
    with pytest.raises(UnsafeOperationException):
        migrate(['bad_rollback_flow_change_char_type_that_safe_app', '0001'])


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.bad_flow_add_column_with_default_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_add_column_with_default():
    # forward
    with pytest.raises(UnsafeOperationException):
        migrate(['bad_flow_add_column_with_default_app'])


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.bad_flow_add_column_with_notnull_default_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_add_column_with_notnull_default():
    # forward
    with pytest.raises(UnsafeOperationException):
        migrate(['bad_flow_add_column_with_notnull_default_app'])


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.bad_flow_add_column_with_notnull_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_add_column_with_notnull():
    # forward
    with pytest.raises(UnsafeOperationException):
        migrate(['bad_flow_add_column_with_notnull_app'])


@skip_for_default_django_backend
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.bad_flow_change_char_type_that_unsafe_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_bad_flow_change_char_type_that_unsafe():
    # forward
    with pytest.raises(UnsafeOperationException):
        migrate(['bad_flow_change_char_type_that_unsafe_app'])
