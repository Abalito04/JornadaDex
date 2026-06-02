# RBAC Matrix

| Module / Action | Company Owner / Jefe | Supervisor | Employee |
| --- | --- | --- | --- |
| Create company workspace | Yes | No | No |
| Login | Yes | Yes | Yes |
| Logout | Yes | Yes | Yes |
| View own profile | Yes | Yes | Yes |
| Change own password | Yes | Yes | Yes |
| Manage company profile | Yes | No | No |
| Manage company users | Yes | No | No |
| Create employee login users | Yes | No | No |
| View employees | Yes | Yes | No |
| Create employees | Yes | Yes | No |
| Update employees | Yes | Yes | No |
| Delete employees | Yes | No | No |
| View areas | Yes | Yes | Yes |
| Manage areas | Yes | No | No |
| View tasks | Yes | Yes | Yes |
| Create tasks | Yes | Yes | No |
| Update tasks | Yes | Yes | No |
| Delete tasks | Yes | No | No |
| Create own time records | Yes | Yes | Yes |
| Create records for employees | Yes | Yes | No |
| View own time records | Yes | Yes | Yes |
| View company time records | Yes | Yes | No |
| Update own time records | Yes | Yes | Yes |
| Update company time records | Yes | Yes | No |
| Delete own time records | Yes | Yes | Yes |
| Delete company time records | Yes | Yes | No |
| View company dashboard | Yes | Yes | Limited |
| View company reports | Yes | Yes | Own only |
| Export company reports | Yes | Yes | Own only |
| View company audit logs | Yes | No | No |

## Role Notes

Company Owner / Jefe:
- Owns the company workspace.
- Has full access to that company's modules and records.
- Cannot access other companies.

Supervisor:
- Has operational management access.
- Can manage employees, tasks and time records inside the same company.
- Cannot manage users, roles, areas or audit logs.
- Cannot access other companies.

Employee:
- Can create and view own records.
- Cannot access other employee records.
- Can export only own data if enabled.
- Cannot access other companies.
