# RBAC Matrix

| Module / Action | Administrator | Supervisor | Employee |
| --- | --- | --- | --- |
| Login | Yes | Yes | Yes |
| Logout | Yes | Yes | Yes |
| View own profile | Yes | Yes | Yes |
| Change own password | Yes | Yes | Yes |
| Manage users | Yes | No | No |
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
| View own time records | Yes | Yes | Yes |
| View all time records | Yes | Yes | No |
| Update own time records | Yes | Yes | Yes |
| Update all time records | Yes | Yes | No |
| Delete own time records | Yes | Yes | Yes |
| Delete all time records | Yes | Yes | No |
| View dashboard | Yes | Yes | Limited |
| View reports | Yes | Yes | Own only |
| Export reports | Yes | Yes | Own only |
| View audit logs | Yes | No | No |

## Role Notes

Administrator:
- Full access to all modules and records.

Supervisor:
- Operational management access.
- Can manage employees, tasks and time records.
- Cannot manage users, roles, areas or audit logs.

Employee:
- Can create and view own records.
- Cannot access other employee records.
- Can export only own data if enabled.
