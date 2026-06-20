# Deployment Guide

## Environment Variables

Use `.env.example` as base:

```text
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=sqlite:///time_control.db
SESSION_COOKIE_SECURE=false
SESSION_LIFETIME_HOURS=12
PUBLIC_SIGNUP_ENABLED=true
SIGNUP_RATE_LIMIT_ATTEMPTS=5
SIGNUP_RATE_LIMIT_WINDOW_MINUTES=60
ENABLE_DEVELOPER_BOOTSTRAP=false
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
```

For production:

```text
SESSION_COOKIE_SECURE=true
SESSION_LIFETIME_HOURS=12
PUBLIC_SIGNUP_ENABLED=true
SIGNUP_RATE_LIMIT_ATTEMPTS=5
SIGNUP_RATE_LIMIT_WINDOW_MINUTES=60
ENABLE_DEVELOPER_BOOTSTRAP=false
TURNSTILE_SITE_KEY=your-cloudflare-turnstile-site-key
TURNSTILE_SECRET_KEY=your-cloudflare-turnstile-secret-key
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
4. Configure Cloudflare Turnstile keys when public signup is enabled.
5. Run behind a reverse proxy with HTTPS.
6. Schedule database backups.
7. Use migrations for schema changes.
8. Restrict access to server logs and environment files.







