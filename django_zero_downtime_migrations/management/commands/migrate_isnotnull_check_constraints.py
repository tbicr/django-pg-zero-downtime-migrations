import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):

    CHECK_CONSTRAINT_REGEXP = re.compile(r'^CHECK \(\((\w+) IS NOT NULL\)\)$')

    def _is_postgres_12(self):
        return connection.pg_version >= 120000

    def _is_postgres_10(self):
        return connection.pg_version >= 100000

    def _can_update_pg_attribute(self):
        sql = (
            "SELECT 1 "
            "FROM information_schema.table_privileges "
            "WHERE table_schema = 'pg_catalog' "
            "AND table_name = 'pg_attribute' "
            "AND privilege_type = 'UPDATE'"
        )
        with connection.temporary_connection() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()
            return result is not None

    def _can_migrate(self):
        return self._is_postgres_12() or (self._is_postgres_10() and self._can_update_pg_attribute())

    def _migrate_for_postgres_12(self, ignore, only):
        with connection.temporary_connection() as cursor:
            for namespace, table, column, name, definition in self._find_constraints():
                if only and name not in only:
                    continue
                if ignore and name in ignore:
                    continue

                cursor.execute('ALTER TABLE %(ns)s.%(table)s ALTER COLUMN %(column)s SET NOT NULL' % {
                    'ns': connection.ops.quote_name(namespace),
                    'table': connection.ops.quote_name(table),
                    'column': connection.ops.quote_name(column),
                })
                cursor.execute('ALTER TABLE %(ns)s.%(table)s DROP CONSTRAINT %(name)s' % {
                    'ns': connection.ops.quote_name(namespace),
                    'table': connection.ops.quote_name(table),
                    'name': connection.ops.quote_name(name),
                })
                self.stdout.write(
                    '%(ns)s.%(table)s %(name)s %(definition)s -> %(ns)s.%(table)s.%(column)s NOT NULL' % {
                        'ns': connection.ops.quote_name(namespace),
                        'table': connection.ops.quote_name(table),
                        'column': connection.ops.quote_name(column),
                        'name': connection.ops.quote_name(name),
                        'definition': definition,
                    })

    def _migrate_for_pg_attributes_update(self, ignore, only):
        with connection.temporary_connection() as cursor:
            for namespace, table, column, name, definition in self._find_constraints():
                if only and name not in only:
                    continue
                if ignore and name in ignore:
                    continue

                cursor.execute(
                    'UPDATE pg_catalog.pg_attribute SET attnotnull = TRUE '
                    'WHERE attrelid = \'%(ns)s.%(table)s\'::regclass::oid '
                    'AND attname = replace(\'%(column)s\', \'"\', \'\')' % {
                        'ns': connection.ops.quote_name(namespace),
                        'table': connection.ops.quote_name(table),
                        'column': connection.ops.quote_name(column),
                    }
                )
                cursor.execute('ALTER TABLE %(ns)s.%(table)s DROP CONSTRAINT %(name)s' % {
                    'ns': connection.ops.quote_name(namespace),
                    'table': connection.ops.quote_name(table),
                    'name': connection.ops.quote_name(name),
                })
                self.stdout.write(
                    '%(ns)s.%(table)s %(name)s %(definition)s -> %(ns)s.%(table)s.%(column)s NOT NULL' % {
                        'ns': connection.ops.quote_name(namespace),
                        'table': connection.ops.quote_name(table),
                        'column': connection.ops.quote_name(column),
                        'name': connection.ops.quote_name(name),
                        'definition': definition,
                    })

    def _migrate(self, ignore, only):
        if self._is_postgres_12():
            self._migrate_for_postgres_12(ignore, only)
        else:
            self._migrate_for_pg_attributes_update(ignore, only)

    def _find_constraints(self):
        sql = (
            "SELECT connamespace::regnamespace, conrelid::regclass, conname, pg_get_constraintdef(oid) "
            "FROM pg_catalog.pg_constraint "
            "WHERE connamespace::regnamespace NOT IN ('pg_catalog', 'information_schema') "
            "AND contype = 'c' "
            "AND conname LIKE '%_notnull'"
        )
        constraints = []
        with connection.temporary_connection() as cursor:
            cursor.execute(sql)
            result = cursor.fetchmany()
            for namespace, table, name, definition in result:
                match = self.CHECK_CONSTRAINT_REGEXP.match(definition)
                if match:
                    column, = match.groups()
                    constraints.append((namespace, table, column, name, definition))

        return sorted(constraints)

    def _list_migrations(self):
        for namespace, table, column, name, definition in self._find_constraints():
            self.stdout.write(
                '%(ns)s.%(table)s %(name)s %(definition)s -> %(ns)s.%(table)s.%(column)s NOT NULL' % {
                    'ns': connection.ops.quote_name(namespace),
                    'table': connection.ops.quote_name(table),
                    'column': connection.ops.quote_name(column),
                    'name': connection.ops.quote_name(name),
                    'definition': definition,
                })

    def add_arguments(self, parser):
        parser.add_argument('-f', '--force', action='store_true', help='Force migration run')
        parser.add_argument('-i', '--ignore', nargs='+', type=str, help='Constraints that ignore for migration')
        parser.add_argument('-o', '--only', nargs='+', type=str, help='Constraints that only should be migrated')
        parser.add_argument('-l', '--list', action='store_true', help='Show list of constraints for migration')

    def handle(self, *args, **options):
        force = options['force']
        ignore = options['ignore']
        only = options['only']
        list = options['list']

        if list:
            self._list_migrations()
            return

        if not force and not self._can_migrate():
            raise CommandError(
                'Can\'t run this command for postgres < 12 and without superuser permissions. (%s)'
                % connection.pg_version
            )

        self._migrate(ignore, only)
