# Development Roadmap

## Phase 1 - Analysis and Architecture

Status: Ready for validation.

Deliverables:
- Functional analysis
- Architecture design
- ER diagram
- Database schema
- API design
- RBAC matrix
- Development roadmap

## Phase 2 - Project Scaffold

Deliverables:
- Flask application factory
- Configuration system
- Extensions setup
- Blueprint registration
- Base templates
- Static asset structure
- Docker and Compose skeleton
- Requirements file
- Company-scoped base context

## Phase 3 - Database Foundation

Deliverables:
- SQLAlchemy models
- Shared timestamp mixin
- Shared soft delete mixin
- Flask-Migrate setup
- Initial migration
- Seed script for initial areas and tasks from prototype

## Phase 4 - Authentication and RBAC

Deliverables:
- Company owner signup
- Login
- Logout
- Session management
- Password hashing
- Role checks
- Protected routes
- User profile
- Employee login provisioning
- Company data isolation checks

## Phase 5 - Core CRUD Modules

Deliverables:
- User management
- Employee management
- Area management
- Task management
- Soft delete behavior
- Server-side validation

## Phase 6 - Time Tracking

Deliverables:
- Time record start form without manual date/time fields
- Finish action with automatic server end time
- Area/task dependent selector
- Hours calculation after finishing
- Active task validation
- Duplicate validation
- List, edit and soft delete records

## Phase 7 - Audit Trail

Deliverables:
- Audit service
- Audit repository
- Automatic audit logging for business actions
- Audit log UI for administrators

## Phase 8 - Dashboard and Reports

Deliverables:
- KPI cards
- Hours by employee chart
- Hours by area chart
- Hours by task chart
- Monthly trend
- Productivity ranking
- Report filters

## Phase 9 - Exports

Deliverables:
- CSV export
- Excel export with openpyxl
- Export audit logging

## Phase 10 - Hardening and Deployment

Deliverables:
- CSRF validation
- Secure cookies by environment
- Error pages
- Dockerfile
- docker-compose.yml
- README
- Deployment guide
- Test plan

## Validation Needed Before Coding

1. Confirm that the first account created for a company is the `Jefe` / company owner.
2. Confirm whether a company owner can create employee users manually or send invitations later.
3. Confirm whether initial project should prioritize a working MVP or full enterprise scope.
4. Confirm whether authentication should use Flask-Login sessions or JWT.
5. Confirm whether the UI should be fully server-rendered or hybrid Jinja2 plus Fetch API.
6. Confirm whether Excel export is required in the first implementation milestone.
7. Confirm that multi-company isolation must be active from day one, even if there is no platform super-admin UI yet.
