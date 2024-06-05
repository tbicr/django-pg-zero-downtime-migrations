import contextlib
import os
import subprocess
from typing import List

from django.conf import settings
from django.db import connection
from django.db.backends.postgresql.base import Database


def one_line_sql(sql: str) -> str:
    return sql.replace("    ", "").replace("\n", " ").replace("( ", "(").replace(" )", ")").replace("  ", " ").strip()


def split_sql_queries(sql: str) -> List[str]:
    return [line for line in sql.splitlines() if line and not line.startswith("--")]


def pg_dump(table: str) -> str:
    host = settings.DATABASES["default"]["HOST"]
    port = settings.DATABASES["default"]["PORT"]
    name = settings.DATABASES["default"]["NAME"]
    user = settings.DB_SUPER_USER
    password = settings.DB_SUPER_PASSWORD
    env = os.environ.copy() | {"PGPASSWORD": password}
    cmd = f"pg_dump -h {host} -p {port} -U {user} -d {name} -s -t {table}"
    popen = subprocess.run(cmd, env=env, text=True, shell=True, capture_output=True, check=True)
    return popen.stdout


@contextlib.contextmanager
def super_user_cursor():
    host = settings.DATABASES["default"]["HOST"]
    port = settings.DATABASES["default"]["PORT"]
    name = settings.DATABASES["default"]["NAME"]
    user = settings.DB_SUPER_USER
    password = settings.DB_SUPER_PASSWORD
    conn = Database.connect(f"host={host} port={port} dbname={name} user={user} password={password}")
    try:
        conn.autocommit = True
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    finally:
        conn.close()


def make_index_invalid(table: str, index: str):
    with super_user_cursor() as cursor:
        cursor.execute("""
            UPDATE pg_index
            SET indisvalid = false
            WHERE indrelid = %s::regclass::oid
            AND indexrelid = %s::regclass::oid
        """, [table, index])
    assert not is_valid_index(table, index)


def is_valid_index(table: str, index: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT indisvalid
            FROM pg_index
            WHERE indrelid = %s::regclass::oid
            AND indexrelid = %s::regclass::oid
        """, [table, index])
        data = cursor.fetchone()
        if data is None:
            raise ValueError(f"index {index} not found for {table}")
        return data[0]


def is_valid_constraint(table: str, constraint: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT convalidated
            FROM pg_constraint
            WHERE conrelid = %s::regclass::oid
            AND conname = %s
        """, [table, constraint])
        data = cursor.fetchone()
        if data is None:
            raise ValueError(f"constraint {constraint} not found for {table}")
        return data[0]
