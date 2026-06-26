# Deployment Guide

## Environment Variables

Use `.env.example` as base for local development:

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
EMAIL_VERIFICATION_REQUIRED=false
EMAIL_VERIFICATION_MAX_AGE_HOURS=24
PASSWORD_RESET_MAX_AGE_MINUTES=60
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_USE_TLS=true
RESEND_API_KEY=
```

For production on Railway:

```text
SESSION_COOKIE_SECURE=true
SESSION_LIFETIME_HOURS=12
PUBLIC_SIGNUP_ENABLED=true
SIGNUP_RATE_LIMIT_ATTEMPTS=5
SIGNUP_RATE_LIMIT_WINDOW_MINUTES=60
ENABLE_DEVELOPER_BOOTSTRAP=false
TURNSTILE_SITE_KEY=your-cloudflare-turnstile-site-key
TURNSTILE_SECRET_KEY=your-cloudflare-turnstile-secret-key
EMAIL_VERIFICATION_REQUIRED=true
EMAIL_VERIFICATION_MAX_AGE_HOURS=24
PASSWORD_RESET_MAX_AGE_MINUTES=60
SMTP_FROM_EMAIL=JornadaDex <onboarding@resend.dev>
RESEND_API_KEY=your-resend-api-key
DATABASE_URL=postgresql+psycopg://user:password@db:5432/time_control
```

If you use a generic SMTP provider instead of Resend API, configure:

```text
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=no-reply@your-domain.example
SMTP_USE_TLS=true
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
5. Configure `RESEND_API_KEY` or SMTP before enabling email verification and password reset emails.
6. Run behind a reverse proxy with HTTPS.
7. Schedule database backups.
8. Use migrations for schema changes.
9. Restrict access to server logs and environment files.
