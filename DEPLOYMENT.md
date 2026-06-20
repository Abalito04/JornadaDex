# Deployment Guide

## Environment Variables

Use `.env.example` as base:

```text
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=sqlite:///time_control.db
SESSION_COOKIE_SECURE=false
```

For production:

```text
SESSION_COOKIE_SECURE=true
PUBLIC_SIGNUP_ENABLED=false
ENABLE_DEVELOPER_BOOTSTRAP=false
DATABASE_URL=postgresql+psycopg://user:password@db:5432/time_control
```

## Development

```powershell
pip install -r requirements.txt
flask init-db
flask run
```

## Docker

```powershell
docker compose up --build
```

Then create the first company owner from `/auth/signup`.

## Production Notes

1. Use PostgreSQL.
2. Set a strong `SECRET_KEY`.
3. Enable secure cookies.
4. Run behind a reverse proxy with HTTPS.
5. Schedule database backups.
6. Use migrations for schema changes.
7. Restrict access to server logs and environment files.

