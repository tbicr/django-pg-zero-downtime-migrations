# django-pg-zero-downtime-migrations
Django postgresql backend that apply migrations with respect to database locks.

## Postgresql locks

Postgres has different lock levels that can conflict with each other https://www.postgresql.org/docs/current/static/explicit-locking.html:

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

- Migration operations work synchronously in one thread and cover schema migrations (data migrations conflict with business logic operations same as business logic conflict concurrently).
- Business logic operations work concurrently.

### Migration locks

| lock                     | operations                                                                                                |
|--------------------------|-----------------------------------------------------------------------------------------------------------|
| `ACCESS EXCLUSIVE`       | `CREATE SEQUENCE`, `DROP SEQUENCE`, `CREATE TABLE`, `DROP TABLE` \*, `ALTER TABLE` \*\*, `DROP INDEX`     |
| `SHARE`                  | `CREATE INDEX`                                                                                            |
| `SHARE UPDATE EXCLUSIVE` | `CREATE INDEX CONCURRENTLY`, `DROP INDEX CONCURRENTLY` \*\*\*, `ALTER TABLE VALIDATE CONSTRAINT` \*\*\*\* |

\*: `CREATE SEQUENCE`, `DROP SEQUENCE`, `CREATE TABLE`, `DROP TABLE` shouldn't have conflicts, because your logic shouldn't operate with it

\*\*: Not all `ALTER TABLE` operations require `ACCESS EXCLUSIVE` lock, but all current django's migrations require it https://github.com/django/django/blob/master/django/db/backends/base/schema.py, https://github.com/django/django/blob/master/django/db/backends/postgresql/schema.py and https://www.postgresql.org/docs/current/static/sql-altertable.html

\*\*\*: Django currently doesn't support `CONCURRENTLY` operations

\*\*\*\*: Django doesn't have `VALIDATE CONSTRAINT` logic, but we will use it for some cases

### Business logic locks

| lock            | operations                   | conflict with lock                                              | conflict with operations                    |
|-----------------|------------------------------|-----------------------------------------------------------------|---------------------------------------------|
| `ACCESS SHARE`  | `SELECT`                     | `ACCESS EXCLUSIVE`                                              | `ALTER TABLE`, `DROP INDEX`                 |
| `ROW SHARE`     | `SELECT FOR UPDATE`          | `ACCESS EXCLUSIVE`, `EXCLUSIVE`                                 | `ALTER TABLE`, `DROP INDEX`                 |
| `ROW EXCLUSIVE` | `INSERT`, `UPDATE`, `DELETE` | `ACCESS EXCLUSIVE`, `EXCLUSIVE`, `SHARE ROW EXCLUSIVE`, `SHARE` | `ALTER TABLE`, `DROP INDEX`, `CREATE INDEX` |

So you can find that all django schema changes for exist table conflicts with business logic, but fortunately we can

## Operations FIFO waiting

![postgresql FIFO](fifo-diagram.png "postgresql FIFO")

Fond same diagram in interesting article http://pankrat.github.io/2015/django-migrations-without-downtimes/.

In this diagram we can extract several metrics:

1. operation time - time what you spend for schema change, so there are issue for long running operation on many rows tables like `CREATE INDEX` or `ALTER TABLE ADD COLUMN SET DEFAULT`, so you need use more save equivalents instead.
2. waiting time - your migration will wait until all transactions will be completed, so there are issue for long running operations/transactions like analytic, so you need avoid it or disable on migration time.
3. queries per second + execution time and connections pool - if you too many queries to table and this queries take long time then this queries can just take all available connections to database until wait for release lock, so look like you need different optimizations there: run migrations when load minimal, decrease queries count and execution time, split you data.
4. too many operations in one transaction - you have issues in all previous points for one operation so if you have many operations in one transaction then you have more chances to get this issues, so you should avoid many operations in one transactions (or event don't run it in transactions at all but you should be more careful when some operation will fail).

## Django migrations hacks:

|  # | name                                          | safe | safe alternative             | description |
|---:|-----------------------------------------------|:----:|:----------------------------:|-------------|
|  1 | `CREATE SEQUENCE`                             | X    |                              | safe operation, because your business logic shouldn't operate with new sequence on migration time
|  2 | `DROP SEQUENCE`                               | X    |                              | safe operation, because your business logic shouldn't operate with this sequence on migration time
|  3 | `CREATE TABLE`                                | X    |                              | safe operation, because your business logic shouldn't operate with new table on migration time
|  4 | `DROP TABLE`                                  | X    |                              | safe operation, because your business logic shouldn't operate with this table on migration time
|  5 | `ALTER TABLE RENAME TO`                       |      | new table and copy           | **unsafe operation**, it's too hard write business logic that operate with two tables simultaneously, so propose `CREATE TABLE` and then copy all data to new table
|  6 | `ALTER TABLE SET TABLESPACE`                  |      | new table and copy           | **unsafe operation**, but probably you don't need it at all or frequently
|  7 | `ALTER TABLE ADD COLUMN`                      | X    |                              | safe operation if without `SET NOT NULL`, `SET DEFAULT`, `PRIMARY KEY`, `UNIQUE`
|  8 | `ALTER TABLE ADD COLUMN SET DEFAULT`          |      | add column and set default   | **unsafe operation**, because you spend time in migration to populate all values in table, so propose `ALTER TABLE ADD COLUMN` and then populate column and then `SET DEFAULT`
|  9 | `ALTER TABLE ADD COLUMN SET NOT NULL`         |      | +/-                          | **unsafe operation**, because doesn't work without `SET DEFAULT`, so propose `ALTER TABLE ADD COLUMN` and then populate column and then `ALTER TABLE ALTER COLUMN SET NOT NULL` \*
| 10 | `ALTER TABLE ADD COLUMN PRIMARY KEY`          |      | new table and copy           | **unsafe operation**, but probably you don't need it at all, because you have `PRIMARY KEY` after `CREATE TABLE`
| 11 | `ALTER TABLE ADD COLUMN UNIQUE`               |      | add index and add constraint | **unsafe operation**, because you spend time in migration to `CREATE INDEX`, so propose `ALTER TABLE ADD COLUMN` and then `CREATE INDEX CONCURRENTLY` and then `ALTER TABLE ADD CONSTRAINT UNIQUE USING INDEX` \*\*
| 12 | `ALTER TABLE ALTER COLUMN TYPE`               |      | ???                          | **unsafe operation** ??? ANY OPERATION INSIDE ???
| 13 | `ALTER TABLE ALTER COLUMN SET NOT NULL`       |      | +/-                          | **unsafe operation**, because you spend time in migration to check that all items in column `NOT NULL` \*
| 14 | `ALTER TABLE ALTER COLUMN DROP NOT NULL`      | X    |                              | safe operation
| 15 | `ALTER TABLE ALTER COLUMN SET DEFAULT`        | X    |                              | safe operation
| 16 | `ALTER TABLE ALTER COLUMN DROP DEFAULT`       | X    |                              | safe operation
| 17 | `ALTER TABLE DROP COLUMN`                     | X    |                              | safe operation, because you business logic shouldn't operate with this column on migration time, however better `ALTER TABLE ALTER COLUMN DROP NOT NULL`, `ALTER TABLE DROP CONSTRAINT` and `DROP INDEX` before
| 18 | `ALTER TABLE RENAME COLUMN`                   |      | new column and copy          | **unsafe operation**, it's too hard write business logic that operate with two columns simultaneously, so propose `ALTER TABLE CREATE COLUMN` and then copy all data to new column
| 19 | `ALTER TABLE ADD CONSTRAINT CHECK`            | X    |                              | safe operation ??? ANY OPERATION INSIDE ???
| 20 | `ALTER TABLE DROP CONSTRAINT` (`CHECK`)       | X    |                              | safe operation
| 21 | `ALTER TABLE ADD CONSTRAINT FOREIGN KEY`      | X    |                              | safe operation, lock two tables ??? ANY OPERATION INSIDE ???
| 22 | `ALTER TABLE DROP CONSTRAINT` (`FOREIGN KEY`) | X    |                              | safe operation, lock two tables
| 23 | `ALTER TABLE ADD CONSTRAINT UNIQUE`           |      | add index and add constraint | **unsafe operation**, because you spend time in migration to create index \*\*
| 24 | `ALTER TABLE DROP CONSTRAINT` (`UNIQUE`)      | X    |                              | safe operation \*\* ??? ANY OPERATION INSIDE ???
| 25 | `ALTER TABLE ADD CONSTRAINT PRIMARY KEY`      |      | new table and copy           | **unsafe operation**, but probably you don't need it at all, because you have `PRIMARY KEY` after `CREATE TABLE`
| 26 | `ALTER TABLE DROP CONSTRAINT` (`PRIMARY KEY`) |      | new table and copy           | **unsafe operation**, but probably you don't need it at all, because you have `PRIMARY KEY` after `CREATE TABLE`
| 27 | `CREATE INDEX`                                |      | `CREATE INDEX CONCURRENTLY`  | **unsafe operation**, because you spend time in migration to create index
| 28 | `DROP INDEX`                                  | X    | `DROP INDEX CONCURRENTLY`    | safe operation ??? ANY OPERATION INSIDE ???

\*: postgresql will check that all items in column `NOT NULL` that take time, lets look this point closely below
\*\*: postgresql will have same behaviour when you skip `ALTER TABLE ADD CONSTRAINT UNIQUE USING INDEX`, lets look this point closely below