ROLE_PERMISSIONS = {
    "user": {"activity:read", "favorite:write"},
    "operator": {"activity:read", "favorite:write", "activity:write", "crawler:operate", "review:operator"},
    "admin": {"*"},
}


def has_permission(user, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(user.role, set())
    return "*" in permissions or permission in permissions
