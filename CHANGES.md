# django-pg-zero-downtime-migrations changelog

## 0.3
  - add django 2.2 support with `Meta.indexes` and `Meta.constraints` attributes

## 0.2
  - add option that allow disable `statement_timeout` for long operations like index creation on constraint validation when statement_timeout set globally

## 0.1.1
  - add long description content type

## 0.1
  - first release:
    - replace default sql queries with more safe
    - add options for `statement_timeout` and `lock_timeout`
    - add option for `NOT NULL` constraint behaviour
    - add option for unsafe operation restriction
