# JornadaDex

Web platform for managing tasks, work time, collaborators, clients, reports, and operational traceability.

## Features

- Task and time tracking
- Collaborator, client, area, and task management
- Operational reports and audit trail
- Clean web interface
- Python/Flask backend

## Tech Stack

- Python / Flask
- SQLite / PostgreSQL
- HTML / CSS / JavaScript

## Getting Started

```bash
# Clone the repo
git clone https://github.com/Abalito04/JornadaDex.git
cd JornadaDex

# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py
```

## Backups de Railway PostgreSQL

La guia completa esta en `docs/BACKUPS.md`.

Backup manual desde Windows:

```powershell
cd "C:\Users\maty0\OneDrive\Escritorio\JornadaDex"
powershell -ExecutionPolicy Bypass -File .\scripts\backup_database.ps1 -PgDumpPath "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
```

Instalar backup automatico diario a las 03:00:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_daily_backup_task.ps1 -Time "03:00" -PgDumpPath "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
```

Antes de ejecutar esos comandos, Windows tiene que tener configurada la `DATABASE_URL` publica de Railway como variable de usuario. No guardar esa URL dentro del repo.

## License

MIT
