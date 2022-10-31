from django.conf import settings
from django.db import IntegrityError, connection
from django.test import modify_settings

import pytest

from django_zero_downtime_migrations.management.commands.migrate_isnotnull_check_constraints import (
    Command as MigrateNotNullCommand
)
from tests.integration import migrate


def run_management_command(params=None):
    command = MigrateNotNullCommand()
    parser = command.create_parser('manage.py', 'migrate_isnotnull_check_constraints')
    options = parser.parse_args(params or [])
    cmd_options = vars(options)
    return command.execute(**cmd_options)


def assert_constraints(null, check):
    with connection.temporary_connection() as cursor:
        cursor.execute(
            'SELECT COUNT(*) FROM pg_catalog.pg_attribute '
            'WHERE attnotnull = TRUE '
            'AND attrelid = \'old_notnull_check_constraint_migration_app_testtable\'::regclass::oid '
            'AND attname = \'field\''
        )
        assert cursor.fetchone()[0] == null

        cursor.execute(
            'SELECT COUNT(*) FROM pg_catalog.pg_constraint '
            'WHERE contype = \'c\''
            'AND conrelid = \'old_notnull_check_constraint_migration_app_testtable\'::regclass::oid'
        )
        assert cursor.fetchone()[0] == check

        with pytest.raises(IntegrityError):
            cursor.execute('INSERT INTO old_notnull_check_constraint_migration_app_testtable VALUES (2, null)')


@pytest.mark.skipif(
    settings.DATABASES['default']['HOST'] not in ['pg12'] and settings.DATABASES['default']['USER'] != 'root',
    reason='superuser permissions required',
)
@pytest.mark.django_db(transaction=True)
@modify_settings(INSTALLED_APPS={'append': 'tests.apps.old_notnull_check_constraint_migration_app'})
def test_migrate_isnotnull_check_constraints():
    migrate()
    assert_constraints(null=0, check=1)
    run_management_command()
    assert_constraints(null=1, check=0)
