# API Design

All API endpoints use English paths and JSON payloads. UI labels remain Spanish.

## Authentication

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | Login user | Public |
| POST | `/api/auth/logout` | Logout user | Authenticated |
| POST | `/api/auth/password-reset/request` | Request reset | Public |
| POST | `/api/auth/password-reset/confirm` | Confirm reset | Public |
| GET | `/api/auth/profile` | Current profile | Authenticated |

## Users

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/users` | List users | Administrator |
| POST | `/api/users` | Create user | Administrator |
| GET | `/api/users/{id}` | Get user | Administrator |
| PUT | `/api/users/{id}` | Update user | Administrator |
| DELETE | `/api/users/{id}` | Soft delete user | Administrator |

## Employees

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/employees` | List employees | Administrator, Supervisor |
| POST | `/api/employees` | Create employee | Administrator, Supervisor |
| GET | `/api/employees/{id}` | Get employee | Administrator, Supervisor |
| PUT | `/api/employees/{id}` | Update employee | Administrator, Supervisor |
| DELETE | `/api/employees/{id}` | Soft delete employee | Administrator |

## Areas

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/areas` | List areas | Authenticated |
| POST | `/api/areas` | Create area | Administrator |
| PUT | `/api/areas/{id}` | Update area | Administrator |
| DELETE | `/api/areas/{id}` | Soft delete area | Administrator |

## Tasks

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/tasks` | List tasks | Authenticated |
| GET | `/api/areas/{area_id}/tasks` | List tasks by area | Authenticated |
| POST | `/api/tasks` | Create task | Administrator, Supervisor |
| PUT | `/api/tasks/{id}` | Update task | Administrator, Supervisor |
| DELETE | `/api/tasks/{id}` | Soft delete task | Administrator |

## Time Records

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/time-records` | List records with filters | Authenticated |
| POST | `/api/time-records` | Create record | Authenticated |
| GET | `/api/time-records/{id}` | Get record | Authenticated |
| PUT | `/api/time-records/{id}` | Update record | Administrator, Supervisor, owner |
| DELETE | `/api/time-records/{id}` | Soft delete record | Administrator, Supervisor, owner |

Create payload:

```json
{
  "employee_id": 1,
  "record_date": "2026-06-01",
  "start_time": "09:00",
  "end_time": "11:30",
  "area_id": 1,
  "task_id": 1,
  "observations": "Detalle opcional"
}
```

Response:

```json
{
  "id": 1,
  "employee_id": 1,
  "record_date": "2026-06-01",
  "start_time": "09:00",
  "end_time": "11:30",
  "hours": "2.50",
  "area_id": 1,
  "task_id": 1,
  "observations": "Detalle opcional"
}
```

## Dashboard

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/dashboard/summary` | Metrics summary | Administrator, Supervisor |
| GET | `/api/dashboard/charts/hours-by-employee` | Chart data | Administrator, Supervisor |
| GET | `/api/dashboard/charts/hours-by-area` | Chart data | Administrator, Supervisor |
| GET | `/api/dashboard/charts/hours-by-task` | Chart data | Administrator, Supervisor |
| GET | `/api/dashboard/charts/monthly-trend` | Chart data | Administrator, Supervisor |

## Reports

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/reports/time-records` | Filtered report | Administrator, Supervisor |
| GET | `/api/reports/time-records/export/csv` | CSV export | Administrator, Supervisor |
| GET | `/api/reports/time-records/export/excel` | Excel export | Administrator, Supervisor |

## Audit

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| GET | `/api/audit-logs` | List audit logs | Administrator |
| GET | `/api/audit-logs/{id}` | Get audit entry | Administrator |
