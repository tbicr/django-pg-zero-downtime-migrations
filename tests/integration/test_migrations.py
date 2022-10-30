from django.conf import settings
from django.test import modify_settings, override_settings

import pytest

from django_zero_downtime_migrations.backends.postgres.schema import (
    UnsafeOperationException
)
from tests import skip_for_default_django_backend
from tests.integration import migrate


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.good_flow_alter_table_with_same_db_table'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow_alter_table_with_same_db_table():
    # forward
    migrate(['good_flow_alter_table_with_same_db_table'])

    # backward
    migrate(['good_flow_alter_table_with_same_db_table', 'zero'])


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.good_flow_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow():
    # forward
    if settings.DATABASES['default']['HOST'] in ['pg14', 'postgis14']:
        # related to https://www.postgresql.org/message-id/3175925.1637428221%40sss.pgh.pa.us bug
        migrate(['good_flow_app', '0045'])
    else:
        migrate(['good_flow_app'])

    # backward
    migrate(['good_flow_app', 'zero'])


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.good_flow_app_concurrently'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=True)
def test_good_flow_create_and_drop_index_concurrently():
    # forward
    migrate(['good_flow_app_concurrently'])

    # backward
    migrate(['good_flow_app_concurrently', 'zero'])


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


@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.decimal_to_float_app'})
@override_settings(ZERO_DOWNTIME_MIGRATIONS_RAISE_FOR_UNSAFE=False)
def test_decimal_to_float_app():
    # forward
    migrate(['decimal_to_float_app'])

    # backward
    migrate(['decimal_to_float_app', 'zero'])
