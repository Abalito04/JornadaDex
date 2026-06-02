# Database Schema

## Tables

### companies

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| name | String(150) | Required, unique |
| tax_id | String(50) | Optional |
| active | Boolean | Default true |
| created_at | DateTime | Required |
| updated_at | DateTime | Required |
| deleted_at | DateTime | Soft delete |
| created_by | Integer | FK users.id |
| updated_by | Integer | FK users.id |
| deleted_by | Integer | FK users.id |

### branches

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| company_id | Integer | FK companies.id |
| name | String(150) | Required |
| address | String(255) | Optional |
| active | Boolean | Default true |
| audit fields | mixed | Standard audit columns |

### departments

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| company_id | Integer | FK companies.id |
| name | String(150) | Required |
| active | Boolean | Default true |
| audit fields | mixed | Standard audit columns |

### users

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| company_id | Integer | FK companies.id |
| username | String(80) | Required, unique |
| email | String(255) | Required, unique |
| password_hash | String(255) | Required |
| role | String(30) | Administrator, Supervisor, Employee |
| is_active | Boolean | Default true |
| last_login_at | DateTime | Optional |
| audit fields | mixed | Standard audit columns |

### employees

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| company_id | Integer | FK companies.id |
| branch_id | Integer | FK branches.id, nullable |
| department_id | Integer | FK departments.id, nullable |
| user_id | Integer | FK users.id, nullable |
| first_name | String(120) | Required |
| last_name | String(120) | Required |
| document_number | String(50) | Required, unique by company |
| email | String(255) | Optional |
| phone | String(60) | Optional |
| position | String(120) | Optional |
| hire_date | Date | Optional |
| active | Boolean | Default true |
| notes | Text | Optional |
| audit fields | mixed | Standard audit columns |

### areas

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| company_id | Integer | FK companies.id |
| name | String(150) | Required, unique by company |
| description | Text | Optional |
| active | Boolean | Default true |
| audit fields | mixed | Standard audit columns |

### tasks

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| area_id | Integer | FK areas.id |
| name | String(200) | Required, unique by area |
| description | Text | Optional |
| active | Boolean | Default true |
| audit fields | mixed | Standard audit columns |

### time_records

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| employee_id | Integer | FK employees.id |
| area_id | Integer | FK areas.id |
| task_id | Integer | FK tasks.id |
| record_date | Date | Required |
| start_time | Time | Required |
| end_time | Time | Required |
| hours | Numeric(8, 2) | Required, calculated |
| observations | Text | Optional |
| audit fields | mixed | Standard audit columns |

Constraints:
- `end_time > start_time`
- no overlapping ranges for same employee and date
- prevent exact duplicate employee/date/start/end/task active entries
- task must belong to selected area

### audit_logs

| Column | Type | Notes |
| --- | --- | --- |
| id | Integer | Primary key |
| user_id | Integer | FK users.id |
| action | String(50) | Required |
| table_name | String(120) | Required |
| record_id | Integer | Optional |
| previous_values | JSON | Optional |
| new_values | JSON | Optional |
| ip_address | String(64) | Optional |
| user_agent | String(500) | Optional |
| created_at | DateTime | Required |

## Indexes

1. `users.email`
2. `users.username`
3. `employees.company_id, employees.document_number`
4. `areas.company_id, areas.name`
5. `tasks.area_id, tasks.name`
6. `time_records.employee_id, time_records.record_date`
7. `time_records.area_id`
8. `time_records.task_id`
9. `audit_logs.user_id, audit_logs.created_at`
10. `audit_logs.table_name, audit_logs.record_id`
