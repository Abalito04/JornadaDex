# TrazaLab

Aplicacion Flask para gestion de empleados, carga de horas, tareas, reportes y auditoria con aislamiento por empresa.

## Funcionalidad incluida

- Alta de empresa con usuario `Jefe`.
- Login por usuario.
- Empleados vinculados a una empresa.
- Usuarios para empleados o supervisores.
- Areas y tareas iniciales tomadas del prototipo HTML.
- Inicio y finalizacion de tareas con fecha y hora automatica del servidor.
- Calculo automatico de horas al finalizar la tarea.
- Dashboard por empresa.
- Reportes con filtros.
- Exportacion CSV y Excel.
- Auditoria por empresa.
- Soft delete para registros principales.

## Arranque local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_APP="run.py"
flask init-db
flask run
```

Abrir:

```text
http://127.0.0.1:5000
```

La primera vez, crear una empresa desde `Crear empresa y jefe`.

## Demo opcional

```powershell
flask create-demo
flask run
```

Credenciales:

```text
usuario: jefe
clave: admin123
```

## Modelo de permisos

- `Company Owner / Jefe`: controla su empresa completa.
- `Supervisor`: gestiona empleados, tareas operativas y registros de la misma empresa.
- `Employee`: carga y consulta sus propios registros.

Ningun usuario puede ver datos de otra empresa.

## Docker

```powershell
docker compose up --build
```

## Estructura

```text
app/
  auth/
  dashboard/
  employees/
  areas/
  time_records/
  reports/
  audit/
  models/
  services/
  permissions/
  templates/
  static/
docs/
```

## Notas tecnicas

- SQLite por defecto en desarrollo.
- `DATABASE_URL` permite cambiar a PostgreSQL.
- Flask-Login maneja sesiones.
- Flask-WTF protege formularios con CSRF.
- SQLAlchemy evita SQL manual inseguro.
- Auditoria registra acciones sensibles por empresa.

