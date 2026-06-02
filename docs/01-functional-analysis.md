# Functional Analysis - Time Control System

## Source Prototype

The source prototype is `control_tiempo_tareas.html`, version 0.1. It defines a Spanish UI for recording time by person, date, schedule, area and task, storing records in browser `localStorage`.

## Functional Scope Extracted From Prototype

### Current Entities

1. Person
   - In the prototype, this is a free text field named `persona`.
   - In the enterprise system, this becomes `Employee`.

2. Area
   - Defined as a fixed JavaScript object key.
   - Must become a database-managed entity.

3. Task
   - Defined as a fixed list under each area.
   - Must become a database-managed entity linked to `Area`.

4. Time Record
   - Current core transactional entity.
   - Stores person, date, start time, end time, calculated hours, area, task and observations.

5. User
   - Not present in the prototype.
   - Required for authentication, authorization, ownership and traceability.

6. Audit Log
   - Not present in the prototype.
   - Required for enterprise traceability.

### Fields

#### Time Record Fields

| UI Label | Prototype ID | Target Field | Required |
| --- | --- | --- | --- |
| Persona | `persona` | `employee_id` | Yes |
| Fecha | `fecha` | `record_date` | Yes |
| Hora desde | `desde` | `start_time` | Yes |
| Hora hasta | `hasta` | `end_time` | Yes |
| Area | `area` | `area_id` | Yes |
| Tarea | `tarea` | `task_id` | Yes |
| Observaciones | `observaciones` | `observations` | No |
| Horas | calculated | `hours` | System calculated |

#### Initial Areas

1. Impositivo
2. Contable y Balances
3. Societario
4. Auditoria y Certificaciones
5. Organizacion Interna

#### Initial Tasks

Impositivo:
- Determinacion y liquidacion de impuestos mensuales
- Determinacion y liquidacion de impuestos anuales
- Fiscalizaciones y requerimientos
- Contingencias tributarias
- Planificacion y estrategia fiscal

Contable y Balances:
- Registracion y cierres contables mensuales
- Registracion y cierres contables anuales
- Confeccion y exposicion de estados contables
- Analisis e interpretacion de resultados
- Auditoria de estados contables
- Informes especiales

Societario:
- Actas y libros societarios
- Tramites y presentaciones externas
- Asesoramiento y estructura societaria

Auditoria y Certificaciones:
- Certificaciones contables e informes especiales

Organizacion Interna:
- Capacitacion
- Reuniones de celulas
- Emision de informes
- Reparaciones y mantenimientos
- Organizacion Jachal
- Administracion metalurgica
- Cuentas corrientes
- Tramites bancarios

## Business Rules

1. A time record requires employee, date, start time, end time, area and task.
2. End time must be greater than start time.
3. Hours are calculated automatically as `(end_time - start_time) / 60`, rounded to two decimals.
4. A task belongs to one area.
5. The task selector depends on the selected area.
6. Empty observations are allowed.
7. Records can be listed after creation.
8. Records can be deleted in the prototype; enterprise version must soft delete.
9. Records can be exported to CSV.
10. Total hours are the sum of all non-deleted record hours.
11. Total records are the count of all non-deleted records.
12. Enterprise version must prevent overlapping schedules per employee and date.
13. Enterprise version must prevent duplicate entries.
14. Enterprise version must record created, updated and deleted metadata.
15. Enterprise version must audit create, update, delete, login, export and password changes.

## Calculations

### Worked Hours

Input:
- `start_time`
- `end_time`

Formula:

```text
start_minutes = start_hour * 60 + start_minute
end_minutes = end_hour * 60 + end_minute
difference = end_minutes - start_minutes
hours = round(difference / 60, 2)
```

Validation:
- If `difference <= 0`, reject the record.

### Dashboard Metrics

1. Active employees: count active employees.
2. Total hours today: sum hours where `record_date = today`.
3. Total hours this week: sum hours in current week.
4. Total hours this month: sum hours in current month.
5. Total records: count active time records.
6. Active areas: count active areas.
7. Active tasks: count active tasks.

## Workflows

### Add Time Record

1. User selects employee.
2. User selects date.
3. User enters start and end time.
4. User selects area.
5. System loads tasks for selected area.
6. User selects task.
7. User optionally enters observations.
8. System validates required fields.
9. System validates time range.
10. System validates no overlap and no duplicate.
11. System calculates hours.
12. System stores the record.
13. System writes audit log.
14. System refreshes list and metrics.

### Export Records

1. User applies optional filters.
2. User requests CSV or Excel export.
3. System validates permissions.
4. System generates export.
5. System writes audit log.

### Delete Record

1. User selects delete.
2. System asks for confirmation.
3. System validates permissions.
4. System sets `deleted_at` and `deleted_by`.
5. System writes audit log.
6. System excludes record from normal lists and metrics.

## Reports

The prototype only exposes a summary and CSV export. Enterprise reports must include:

1. Hours per employee.
2. Hours per area.
3. Hours per task.
4. Employee productivity.
5. Monthly productivity.
6. Area productivity.

Filters:
- Employee
- Area
- Task
- Date range
- Month
- Year

## User Interactions

1. Form input.
2. Dependent area/task selection.
3. Add record.
4. Delete record.
5. Delete all records.
6. Export CSV.
7. View total hours.
8. View total records.
9. View records table.

## Current Limitations

1. No authentication.
2. No users or roles.
3. No SQL database.
4. Data stored only in browser `localStorage`.
5. No centralized employee catalog.
6. Person is free text, causing duplicates and inconsistent names.
7. Areas and tasks are hardcoded.
8. No audit trail.
9. No soft delete.
10. No server-side validation.
11. No overlap prevention.
12. No duplicate prevention.
13. No Excel export.
14. No dashboards with charts.
15. No advanced reporting.
16. No deployment model.
17. No CSRF protection.
18. No production security controls.
19. No backup or migration strategy.
20. No multi-company readiness.

## Missing Enterprise Features

1. Authentication and secure sessions.
2. RBAC permissions.
3. User management.
4. Employee management.
5. Dynamic area and task administration.
6. SQL persistence.
7. Audit trail.
8. Soft delete.
9. Reporting module.
10. Dashboard module.
11. CSV and Excel exports.
12. API layer.
13. Repository and service layers.
14. Database migrations.
15. Seed data.
16. Docker deployment.
17. Environment-based configuration.
18. Production database compatibility.
19. Future multi-company design.
20. Testable modular structure.
