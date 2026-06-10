ROLE_EMPLOYEE = "Employee"
ROLE_SUPERVISOR = "Supervisor"
ROLE_OWNER = "Owner"
ROLE_DEVELOPER = "Developer"
LEGACY_ADMIN = "Administrator"

COMPANY_ROLES = (ROLE_EMPLOYEE, ROLE_SUPERVISOR, ROLE_OWNER)
PLATFORM_ROLES = COMPANY_ROLES + (ROLE_DEVELOPER,)

ROLE_LABELS = {
    ROLE_EMPLOYEE: "Empleado",
    ROLE_SUPERVISOR: "Supervisor",
    ROLE_OWNER: "Dueño",
    ROLE_DEVELOPER: "Developer",
    LEGACY_ADMIN: "Dueño",
}


def normalize_role(role, allow_developer=False):
    if role == LEGACY_ADMIN:
        return ROLE_OWNER
    allowed_roles = PLATFORM_ROLES if allow_developer else COMPANY_ROLES
    return role if role in allowed_roles else ROLE_EMPLOYEE


def role_label(role, is_company_owner=False, is_platform_admin=False):
    if is_platform_admin:
        return ROLE_LABELS[ROLE_DEVELOPER]
    if is_company_owner:
        return ROLE_LABELS[ROLE_OWNER]
    return ROLE_LABELS.get(role, role or ROLE_LABELS[ROLE_EMPLOYEE])
