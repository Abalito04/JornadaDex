# Migrations

This project is configured for Flask-Migrate.

Initial development can start with:

```text
flask init-db
```

When schema changes need versioning:

```text
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```
