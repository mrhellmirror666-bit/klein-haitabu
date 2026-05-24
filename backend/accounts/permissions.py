from .models import User


def is_admin(user):
    return user.is_authenticated and user.is_platform_admin


def is_normal_user(user):
    return user.is_authenticated and user.role == User.Role.USER


def can_view_event(user, event=None):
    return user.is_authenticated


def can_create_event(user):
    return is_admin(user) or is_normal_user(user)


def can_edit_event(user, event):
    if is_admin(user):
        return True
    if is_normal_user(user):
        return event.created_by_id == user.id
    return False
