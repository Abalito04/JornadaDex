# Backups diarios de PostgreSQL

Este proyecto usa PostgreSQL en Railway. El backup correcto es de la base completa: ahi quedan todas las empresas, usuarios, registros horarios, clientes, areas y tareas.

## 1. Instalar herramientas de PostgreSQL

En Windows necesitas tener disponible `pg_dump` y `pg_restore`. Si instalas PostgreSQL, marca la opcion de command line tools y verifica:

```powershell
pg_dump --version
pg_restore --version
```

Si Windows no los encuentra, podes pasar la ruta completa a `pg_dump.exe` cuando ejecutes el script.

## 2. Configurar DATABASE_URL

Copia la `DATABASE_URL` de Railway y guardala como variable de usuario de Windows:

```powershell
[Environment]::SetEnvironmentVariable("DATABASE_URL", "postgresql://USUARIO:PASSWORD@HOST:PUERTO/DB", "User")
```

Cerra y abri PowerShell para que tome la variable nueva. No guardes esa URL en Git ni en archivos del proyecto.

## 3. Probar un backup manual

Desde la carpeta del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_database.ps1
```

Esto crea archivos en `backups/`:

- `jornadadex-YYYYMMDD-HHMMSS.dump`: backup en formato custom de PostgreSQL.
- `jornadadex-YYYYMMDD-HHMMSS.dump.sha256`: checksum para validar integridad.
- `backup.log`: historial simple de ejecuciones.

Por defecto conserva 30 dias de backups.

## 4. Programar backup diario

Para instalar una tarea diaria a las 03:00:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_daily_backup_task.ps1 -Time "03:00" -PgDumpPath "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
```

La tarea queda en el Programador de tareas de Windows con el nombre `JornadaDex Daily PostgreSQL Backup`.

Importante: este backup automatico corre cuando tu PC esta prendida. Si esta apagada a esa hora, Windows intentara ejecutarlo cuando vuelva a estar disponible.

## 5. Probar restore

No restaures sobre produccion. Crea una base PostgreSQL de prueba y carga su URL como `TEST_DATABASE_URL`:

```powershell
[Environment]::SetEnvironmentVariable("TEST_DATABASE_URL", "postgresql://USUARIO:PASSWORD@HOST:PUERTO/DB_PRUEBA", "User")
```

Luego ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restore_database.ps1 -BackupFile .\backups\jornadadex-YYYYMMDD-HHMMSS.dump
```

## Recomendacion operativa

- Backup diario automatico.
- Restore de prueba una vez por mes.
- Copia adicional fuera de la PC, por ejemplo Google Drive, OneDrive o un storage dedicado.
- Mas adelante: automatizar subida a Cloudflare R2, S3 o similar para no depender de tu computadora.

