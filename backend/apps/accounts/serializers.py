from .models import User


def serialize_user(user: User) -> dict:
    return {
        "id": str(user.pk),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
    }
