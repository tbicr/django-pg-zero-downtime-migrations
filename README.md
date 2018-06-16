# django-pg-zero-downtime-migrations
Django postgresql backend that apply migrations with respect to database locks.

## Postgresql locks

Postgres has different lock levels that can conflic with each ather https://www.postgresql.org/docs/current/static/explicit-locking.html:

|                          | `ACCESS SHARE` | `ROW SHARE` | `ROW EXCLUSIVE` | `SHARE UPDATE EXCLUSIVE` | `SHARE` | `SHARE ROW EXCLUSIVE` | `EXCLUSIVE` | `ACCESS EXCLUSIVE` |
|--------------------------|:--------------:|:-----------:|:---------------:|:------------------------:|:-------:|:---------------------:|:-----------:|:------------------:|
| `ACCESS SHARE`           |                |             |                 |                          |         |                       |             | X                  |
| `ROW SHARE`              |                |             |                 |                          |         |                       | X           | X                  |
| `ROW EXCLUSIVE`          |                |             |                 |                          | X       | X                     | X           | X                  |
| `SHARE UPDATE EXCLUSIVE` |                |             |                 | X                        | X       | X                     | X           | X                  |
| `SHARE`                  |                |             | X               | X                        |         | X                     | X           | X                  |
| `SHARE ROW EXCLUSIVE`    |                |             | X               | X                        | X       | X                     | X           | X                  |
| `EXCLUSIVE`              |                | X           | X               | X                        | X       | X                     | X           | X                  |
| `ACCESS EXCLUSIVE`       | X              | X           | X               | X                        | X       | X                     | X           | X                  |

## Migration and business logic locks

Lets split this lock to migration and business logic operations.

- Migration operations work synchronously in one thread and cover schema migrations (data migrations conflic with business logic operations same as business logic conflict concurently).
- Business logic operations work concurently.

### Migration locks

| lock                     | operations                                                                                                |
|--------------------------|-----------------------------------------------------------------------------------------------------------|
| `ACCESS EXCLUSIVE`       | `CREATE SEQUENCE`, `DROP SEQUENCE`, `CREATE TABLE`, `DROP TABLE` \*, `ALTER TABLE` \*\*, `DROP INDEX`     |
| `SHARE`                  | `CREATE INDEX`                                                                                            |
| `SHARE UPDATE EXCLUSIVE` | `CREATE INDEX CONCURRENTLY`, `DROP INDEX CONCURRENTLY` \*\*\*, `ALTER TABLE VALIDATE CONSTRAINT` \*\*\*\* |

\*: `CREATE SEQUENCE`, `DROP SEQUENCE`, `CREATE TABLE`, `DROP TABLE` shouldn't have conflicts, because your logic shouldn't operate with it

\*\*: Not all `ALTER TABLE` operations require `ACCESS EXCLUSIVE` lock, but all current django's migrations requre it https://github.com/django/django/blob/master/django/db/backends/base/schema.py, https://github.com/django/django/blob/master/django/db/backends/postgresql/schema.py and https://www.postgresql.org/docs/current/static/sql-altertable.html

\*\*\*: Django currently doesn't support concurently operations

\*\*\*\*: Django doesn't have `VALIDATE CONSTRAINT` logic, but we will use it for some cases

### Business logic locks

| lock            | operations                   | conflict with lock                                              | conflict with operations                    |
|-----------------|------------------------------|-----------------------------------------------------------------|---------------------------------------------|
| `ACCESS SHARE`  | `SELECT`                     | `ACCESS EXCLUSIVE`                                              | `ALTER TABLE`, `DROP INDEX`                 |
| `ROW SHARE`     | `SELECT FOR UPDATE`          | `ACCESS EXCLUSIVE`, `EXCLUSIVE`                                 | `ALTER TABLE`, `DROP INDEX`                 |
| `ROW EXCLUSIVE` | `INSERT`, `UPDATE`, `DELETE` | `ACCESS EXCLUSIVE`, `EXCLUSIVE`, `SHARE ROW EXCLUSIVE`, `SHARE` | `ALTER TABLE`, `DROP INDEX`, `CREATE INDEX` |

So you can find that all django schema changes for exist table conflicts with business logic.
